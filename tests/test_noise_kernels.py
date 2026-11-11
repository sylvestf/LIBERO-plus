import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.ndimage import zoom as scizoom

KERNELS = Path(__file__).resolve().parents[1] / "libero" / "libero" / "envs" / "noise_kernels.py"


# load the module from its file, so robosuite and the assets are not needed
def load_kernels(block_numba=False):
    saved = sys.modules.get("numba")
    if block_numba:
        sys.modules["numba"] = None  # makes `from numba import njit` raise ImportError
    try:
        spec = importlib.util.spec_from_file_location("noise_kernels_under_test", KERNELS)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if block_numba:
            if saved is None:
                del sys.modules["numba"]
            else:
                sys.modules["numba"] = saved


kernels = load_kernels()

# (sigma, max_delta, iterations) and zoom factors per severity, as in env_wrapper.py
GLASS = [(0.5, 1, 3), (0.7, 1, 3), (0.9, 2, 3), (1.0, 2, 2), (1.1, 3, 2), (1.3, 3, 2), (1.5, 4, 2), (1.8, 4, 2), (2.2, 5, 1), (2.5, 5, 1)]
ZOOM = [np.arange(1, 1.11, 0.01), np.arange(1, 1.16, 0.01), np.arange(1, 1.21, 0.02), np.arange(1, 1.26, 0.02),
        np.arange(1, 1.31, 0.03), np.arange(1, 1.36, 0.01), np.arange(1, 1.41, 0.01), np.arange(1, 1.46, 0.02),
        np.arange(1, 1.51, 0.02), np.arange(1, 1.56, 0.03)]
SIZES = (128, 256)
# at 160 and 320 px the last zoom coordinate can round past the input, where scipy returns 0
ZOOM_SIZES = (128, 160, 256, 320)


def glass_loop(x, c):
    # glass_blur's loop in env_wrapper.py, unchanged
    height_x, weight_x = x.shape[0], x.shape[1]
    for i in range(c[2]):
        for h in range(height_x - c[1], c[1], -1):
            for w in range(weight_x - c[1], c[1], -1):
                dx, dy = np.random.randint(-c[1], c[1], size=(2,))
                h_prime, w_prime = h + dy, w + dx
                # swap
                x[h, w], x[h_prime, w_prime] = x[h_prime, w_prime], x[h, w]
    return x


def clipped_zoom(img, zoom_factor):
    # env_wrapper.py, unchanged
    h = img.shape[0]
    ch = int(np.ceil(h / float(zoom_factor)))
    top = (h - ch) // 2
    img = scizoom(img[top:top + ch, top:top + ch], (zoom_factor, zoom_factor, 1), order=1)
    trim_top = (img.shape[0] - h) // 2
    return img[trim_top:trim_top + h, trim_top:trim_top + h]


def same_rng_state(a, b):
    return a[0] == b[0] and np.array_equal(a[1], b[1]) and a[2:] == b[2:]


@unittest.skipIf(not kernels.NUMBA_AVAILABLE, "numba is not installed")
class NoiseKernelTest(unittest.TestCase):
    def test_glass_blur_shuffle_matches_loop_and_rng_state(self):
        rng = np.random.default_rng(0)
        for size in SIZES:
            for seed in range(3):
                image = (rng.random((size, size, 3)) * 255).astype(np.uint8)
                for severity, c in enumerate(GLASS, 1):
                    with self.subTest(size=size, seed=seed, severity=severity):
                        np.random.seed(seed)
                        expected = glass_loop(image.copy(), c)
                        expected_state = np.random.get_state()
                        np.random.seed(seed)
                        actual = kernels.shuffle_pixels(image.copy(), c[1], c[2])
                        self.assertTrue(np.array_equal(expected, actual))
                        self.assertTrue(same_rng_state(expected_state, np.random.get_state()))

    def test_zoom_blur_sum_matches_loop(self):
        rng = np.random.default_rng(1)
        for size in ZOOM_SIZES:
            for trial in range(3):
                x = rng.random((size, size, 3)).astype(np.float32)
                for severity, factors in enumerate(ZOOM, 1):
                    with self.subTest(size=size, trial=trial, severity=severity):
                        expected = np.zeros_like(x)
                        for zoom_factor in factors:
                            expected += clipped_zoom(x, zoom_factor)
                        actual = kernels.zoom_sum(x, factors, np.zeros_like(x))
                        self.assertEqual(actual.dtype, np.float32)
                        self.assertTrue(np.array_equal(expected, actual))


class OptionalNumbaTest(unittest.TestCase):
    def test_without_numba_the_loops_are_used(self):
        module = load_kernels(block_numba=True)
        self.assertFalse(module.NUMBA_AVAILABLE)


if __name__ == "__main__":
    unittest.main()
