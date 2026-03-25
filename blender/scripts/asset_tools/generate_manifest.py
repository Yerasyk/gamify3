"""Generate manifest.json for the currently open asset blend file."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _repo_root_from_blend(blend_path: Path) -> Path:
    parts = blend_path.parts
    if "blender" in parts:
        blender_idx = parts.index("blender")
        return Path(*parts[:blender_idx])
    return blend_path.parent


def _compute_dimensions() -> dict[str, float]:
    import bpy  # type: ignore

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    for obj in mesh_objects:
        half_x = abs(float(obj.dimensions.x)) / 2.0
        half_y = abs(float(obj.dimensions.y)) / 2.0
        half_z = abs(float(obj.dimensions.z)) / 2.0
        min_x = min(min_x, float(obj.location.x) - half_x)
        min_y = min(min_y, float(obj.location.y) - half_y)
        min_z = min(min_z, float(obj.location.z) - half_z)
        max_x = max(max_x, float(obj.location.x) + half_x)
        max_y = max(max_y, float(obj.location.y) + half_y)
        max_z = max(max_z, float(obj.location.z) + half_z)

    return {
        "x": round(max_x - min_x, 6),
        "y": round(max_y - min_y, 6),
        "z": round(max_z - min_z, 6),
    }


def main() -> None:
    try:
        import bpy  # type: ignore
    except ImportError as exc:
        raise SystemExit("This script must run inside Blender (bpy not available).") from exc

    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise SystemExit("Open a saved .blend file before running generate_manifest.py")

    repo_root = _repo_root_from_blend(blend_path)
    category = blend_path.parent.name
    asset_name = blend_path.stem
    asset_type = category if category in {"props", "characters", "modular", "materials"} else "props"
    asset_type = {
        "props": "prop",
        "characters": "character",
        "modular": "modular",
        "materials": "material",
    }.get(asset_type, "prop")

    export_dir = repo_root / "exports" / "assets" / category / asset_name
    glb_path = export_dir / f"{asset_name}.glb"
    manifest_path = export_dir / "manifest.json"
    export_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0",
        "asset_id": f"{asset_type}_{asset_name}",
        "asset_type": asset_type,
        "source_file": str(blend_path.relative_to(repo_root)).replace("\\", "/"),
        "exported_glb": str(glb_path.relative_to(repo_root)).replace("\\", "/"),
        "export_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "blender_version": ".".join(str(part) for part in bpy.app.version[:3]),
        "dimensions": _compute_dimensions(),
        "origin": "center_bottom",
        "custom_properties": {},
    }

    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    print(f"Generated manifest: {manifest_path}")


if __name__ == "__main__":
    main()
