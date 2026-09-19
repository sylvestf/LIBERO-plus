# Optional object densities

## Ready-to-run reference profile

After installing LIBERO-plus's required `assets.zip` as described in the main README, run this from the LIBERO-plus repository root:

```bash
export LIBERO_OBJECT_DENSITY_CONFIG="$PWD/docs/reference_object_densities.json"
```

Then run LIBERO-plus normally in the same shell. Unset the variable to use the released benchmark parameters. The bundled profile covers all 39 inherited non-articulated LIBERO object categories, without requiring users to write object-by-object values. This is an **unmeasured sensitivity-study scenario**, not a calibrated correction or a change to the default benchmark. Report scores from it separately from official scores.

The [mass audit](reference_object_density_audit.csv) lists original and reference collision-body masses for the 36 inherited categories present in the [published asset ZIP](https://huggingface.co/datasets/Sylvest/LIBERO-plus/tree/main) at dataset revision `dd2bd61b7d9a6fef1abc52d606e983b41886a149`. Their collision geometries match original LIBERO exactly and specify `density="100"` kg/m³; the same reference values therefore produce the same nominal masses. All 36 original/reference masses were checked by compiling isolated MuJoCo collision-geom models from the ZIP's XML files. The registered `cherries`, `corn`, and `mayo` XML assets are absent from that ZIP; their profile entries are provisional and have no mass claim.

LIBERO-plus also registers 867 new object categories from the separately distributed assets. Their collision geoms are predominantly meshes with MuJoCo default-class properties rather than the inherited 100 kg/m³ boxes. This profile leaves those new objects unchanged: copying LIBERO's effective densities onto different collision geometry would not establish sensible masses. The values here are **effective densities for simplified collision geometry**, not measured material densities. Full task rollout validation remains pending.

## Custom profile

Set `LIBERO_OBJECT_DENSITY_CONFIG` to a JSON file mapping a movable object category or instance to a density in **kg/m³**:

```json
{
  "porcelain_mug": 800,
  "porcelain_mug_1": 950
}
```

```bash
export LIBERO_OBJECT_DENSITY_CONFIG=/absolute/path/object_densities.json
```

An instance entry takes priority over its category entry. Objects absent from the file retain their existing XML. The override changes only collision geoms (group 0) before the task XML is assembled and MuJoCo compiles it. MuJoCo derives mass and inertia from those geoms when no explicit mass or inertial element overrides them; the loader rejects an override on an object with either explicit setting. The option does not change visual meshes, contact geometry, friction, or fixtures.

For numbered custom objects, use the runtime `category_name` as the JSON key (for example, `apple_1`), which can differ from the BDDL registry spelling (`apple__1`).

The file is read once per path in each process. Record its contents and the effective compiled body masses with any results. Changing density changes task dynamics and can invalidate comparisons with previously reported benchmark scores. The values above are format examples, **not measured or recommended physical densities**.
