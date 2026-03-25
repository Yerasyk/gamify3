"""Utility helpers for Gamify Blender MCP handlers."""

from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

import bpy


def _repo_root_from_blend(blend_path: Path) -> Path:
    parts = blend_path.parts
    if "blender" in parts:
        blender_idx = parts.index("blender")
        return Path(*parts[:blender_idx])
    return blend_path.parent


def get_repo_root() -> Path:
    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise RuntimeError("Open a saved .blend file before using Blender MCP tools")
    return _repo_root_from_blend(blend_path)


def _ensure_repo_import_path() -> None:
    root = get_repo_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _load_module(module_name: str) -> ModuleType:
    _ensure_repo_import_path()
    return importlib.import_module(module_name)


def resolve_asset_export_path() -> Path:
    blend_path = Path(bpy.data.filepath)
    module = _load_module("blender.scripts.asset_tools.export_glb")
    return module._resolve_output_path(blend_path)


def export_scene_glb(output_path: Path, include_lights: bool) -> Path:
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
        export_lights=include_lights,
        export_animations=False,
        check_existing=False,
    )
    return output_path


def compute_manifest_data(category: str | None = None) -> dict[str, Any]:
    blend_path = Path(bpy.data.filepath)
    module = _load_module("blender.scripts.asset_tools.generate_manifest")
    repo_root = _repo_root_from_blend(blend_path)
    use_category = category or blend_path.parent.name
    asset_name = blend_path.stem
    asset_type = use_category if use_category in {"props", "characters", "modular", "materials"} else "props"
    asset_type = {
        "props": "prop",
        "characters": "character",
        "modular": "modular",
        "materials": "material",
    }.get(asset_type, "prop")
    export_dir = repo_root / "exports" / "assets" / use_category / asset_name
    glb_path = export_dir / f"{asset_name}.glb"
    manifest_path = export_dir / "manifest.json"
    export_dir.mkdir(parents=True, exist_ok=True)

    return {
        "path": manifest_path,
        "payload": {
            "schema_version": "1.0",
            "asset_id": f"{asset_type}_{asset_name}",
            "asset_type": asset_type,
            "source_file": str(blend_path.relative_to(repo_root)).replace("\\", "/"),
            "exported_glb": str(glb_path.relative_to(repo_root)).replace("\\", "/"),
            "export_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "blender_version": ".".join(str(part) for part in bpy.app.version[:3]),
            "dimensions": module._compute_dimensions(),
            "origin": "center_bottom",
            "custom_properties": {},
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def normalize_marker_id(name: str) -> str:
    module = _load_module("blender.scripts.world_tools.extract_markers")
    return module._normalize_id(name)


def marker_type(marker_id: str) -> str:
    module = _load_module("blender.scripts.world_tools.extract_markers")
    return module._marker_type(marker_id)


def collect_world_dependencies(repo_root: Path) -> list[dict[str, str]]:
    module = _load_module("blender.scripts.world_tools.export_world_glb")
    return module._collect_asset_dependencies(repo_root)
