# Optional object densities

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

The file is read once per path in each process. Record its contents and the effective compiled body masses with any results. Changing density changes task dynamics and can invalidate comparisons with previously reported benchmark scores. The values above are format examples, **not measured or recommended physical densities**.
