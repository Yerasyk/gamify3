"""Export world GLB and write world manifest.json."""

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


def _collect_asset_dependencies(repo_root: Path) -> list[dict[str, str]]:
    dependencies: list[dict[str, str]] = []
    for manifest_path in sorted((repo_root / "exports" / "assets").glob("**/manifest.json")):
        try:
            with manifest_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            asset_id = payload.get("asset_id")
            if isinstance(asset_id, str) and asset_id:
                dependencies.append(
                    {
                        "asset_id": asset_id,
                        "manifest_path": str(manifest_path.relative_to(repo_root)).replace("\\", "/"),
                    }
                )
        except (OSError, json.JSONDecodeError):
            continue
    return dependencies


def main() -> None:
    try:
        import bpy  # type: ignore
    except ImportError as exc:
        raise SystemExit("This script must run inside Blender (bpy not available).") from exc

    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise SystemExit("Open a saved .blend file before running export_world_glb.py")

    repo_root = _repo_root_from_blend(blend_path)
    world_id = blend_path.stem
    export_dir = repo_root / "exports" / "worlds" / world_id
    export_dir.mkdir(parents=True, exist_ok=True)

    glb_path = export_dir / f"{world_id}.glb"
    markers_path = blend_path.parent / "markers.json"
    manifest_path = export_dir / "manifest.json"

    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_colors=True,
        export_cameras=False,
        export_lights=True,
        export_animations=False,
        check_existing=False,
    )

    manifest = {
        "schema_version": "1.0",
        "world_id": world_id,
        "source_file": str(blend_path.relative_to(repo_root)).replace("\\", "/"),
        "exported_glb": str(glb_path.relative_to(repo_root)).replace("\\", "/"),
        "markers_file": str(markers_path.relative_to(repo_root)).replace("\\", "/"),
        "export_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "asset_dependencies": _collect_asset_dependencies(repo_root),
    }

    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    print(f"Exported world GLB: {glb_path}")
    print(f"Generated world manifest: {manifest_path}")


if __name__ == "__main__":
    main()
