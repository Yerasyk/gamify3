# Conventions

## Files

- Blender files use `snake_case.blend`.
- Godot scenes use `PascalCase.tscn`.
- Godot scripts use `snake_case.gd`.
- Python scripts use `snake_case.py`.
- Export metadata files are always named `manifest.json`.

## Identifiers

- Asset IDs use `category_name` like `prop_crate_wooden`.
- World IDs use `level_NN` like `level_01`.
- Marker IDs use `marker_type_name` like `spawn_player`.

## Directory Rules

- Blender sources live under `blender/`.
- Export artifacts live under `exports/`.
- Validation schemas and scripts live under `validation/`.
