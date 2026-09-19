import importlib.util
import pathlib
import random
import sys
import types
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_task_orders(global_seed):
    """Load the benchmark module without importing simulator dependencies."""
    random.seed(global_seed)

    libero = types.ModuleType("libero")
    libero.__path__ = []
    libero_libero = types.ModuleType("libero.libero")
    libero_libero.__path__ = []
    libero_libero.get_libero_path = lambda _: "/unused"
    sys.modules["libero"] = libero
    sys.modules["libero.libero"] = libero_libero

    torch = types.ModuleType("torch")
    torch.load = lambda _: None
    sys.modules["torch"] = torch

    envs = types.ModuleType("libero.libero.envs")
    envs.__path__ = []
    sys.modules["libero.libero.envs"] = envs
    bddl_utils = types.ModuleType("libero.libero.envs.bddl_utils")
    bddl_utils.get_problem_info = lambda _: {"language_instruction": "stub"}
    sys.modules["libero.libero.envs.bddl_utils"] = bddl_utils

    benchmark = types.ModuleType("libero.libero.benchmark")
    benchmark.__path__ = []
    sys.modules["libero.libero.benchmark"] = benchmark

    task_map_path = (
        REPO_ROOT / "libero/libero/benchmark/libero_suite_task_map.py"
    )
    task_map_spec = importlib.util.spec_from_file_location(
        "libero.libero.benchmark.libero_suite_task_map", task_map_path
    )
    task_map = importlib.util.module_from_spec(task_map_spec)
    sys.modules[task_map_spec.name] = task_map
    task_map_spec.loader.exec_module(task_map)

    benchmark_path = REPO_ROOT / "libero/libero/benchmark/__init__.py"
    benchmark_spec = importlib.util.spec_from_file_location(
        "libero.libero.benchmark",
        benchmark_path,
        submodule_search_locations=[str(benchmark_path.parent)],
    )
    benchmark = importlib.util.module_from_spec(benchmark_spec)
    sys.modules[benchmark_spec.name] = benchmark
    benchmark_spec.loader.exec_module(benchmark)
    return benchmark.task_order_dict


class TaskOrderReproducibilityTest(unittest.TestCase):
    def test_non_default_orders_do_not_depend_on_global_random_seed(self):
        orders_from_seed_1 = load_task_orders(1)
        orders_from_seed_2 = load_task_orders(2)

        self.assertEqual(orders_from_seed_1, orders_from_seed_2)

    def test_building_task_orders_does_not_advance_global_random_state(self):
        random.seed(123)
        expected_next_value = random.random()

        load_task_orders(123)
        actual_next_value = random.random()

        self.assertEqual(expected_next_value, actual_next_value)


if __name__ == "__main__":
    unittest.main()
