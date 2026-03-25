"""Extract EMPTY objects into a world markers.json file."""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root_from_blend(blend_path: Path) -> Path:
    parts = blend_path.parts
    if "blender" in parts:
        blender_idx = parts.index("blender")
        return Path(*parts[:blender_idx])
    return blend_path.parent


def _normalize_id(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_")


def _marker_type(marker_id: str) -> str:
    prefix = marker_id.split("_", 1)[0]
    allowed = {"spawn", "trigger", "waypoint", "light", "sound"}
    return prefix if prefix in allowed else "custom"


def main() -> None:
    try:
        import bpy  # type: ignore
    except ImportError as exc:
        raise SystemExit("This script must run inside Blender (bpy not available).") from exc

    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise SystemExit("Open a saved .blend file before running extract_markers.py")

    repo_root = _repo_root_from_blend(blend_path)
    world_id = _normalize_id(blend_path.stem)
    output_path = blend_path.parent / "markers.json"

    markers = []
    for obj in bpy.context.scene.objects:
        if obj.type != "EMPTY":
            continue
        marker_id = _normalize_id(obj.name)
        markers.append(
            {
                "marker_id": marker_id,
                "marker_type": _marker_type(marker_id),
                "position": [round(value, 6) for value in obj.location],
                "rotation": [round(value, 6) for value in obj.rotation_euler],
                "properties": {},
            }
        )

    payload = {"schema_version": "1.0", "world_id": world_id, "markers": markers}
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    rel_path = str(output_path.relative_to(repo_root)).replace("\\", "/")
    print(f"Extracted markers: {rel_path}")


if __name__ == "__main__":
    main()
