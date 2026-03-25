"""Export the open Blender asset file to deterministic GLB output."""

from __future__ import annotations

from pathlib import Path


def _repo_root_from_blend(blend_path: Path) -> Path:
    parts = blend_path.parts
    if "blender" in parts:
        blender_idx = parts.index("blender")
        return Path(*parts[:blender_idx])
    return blend_path.parent


def _resolve_output_path(blend_path: Path) -> Path:
    # Expected source shape: <repo>/blender/assets/<category>/<asset_name>.blend
    category = blend_path.parent.name
    asset_name = blend_path.stem
    repo_root = _repo_root_from_blend(blend_path)
    return repo_root / "exports" / "assets" / category / asset_name / f"{asset_name}.glb"


def main() -> None:
    try:
        import bpy  # type: ignore
    except ImportError as exc:
        raise SystemExit("This script must run inside Blender (bpy not available).") from exc

    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise SystemExit("Open a saved .blend file before running export_glb.py")

    output_path = _resolve_output_path(blend_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
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
        export_lights=False,
        export_animations=False,
        check_existing=False,
    )

    print(f"Exported GLB: {output_path}")


if __name__ == "__main__":
    main()
