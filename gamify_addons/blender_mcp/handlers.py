"""Command handlers for the Gamify Blender MCP socket server."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bpy

from . import socket_server, utils


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method")
    params = request.get("params") or {}
    if not isinstance(method, str):
        raise ValueError("Missing 'method' string")
    if not isinstance(params, dict):
        raise ValueError("'params' must be an object")

    handlers: dict[str, Any] = {
        "ping": _handle_ping,
        "get_scene_state": _handle_get_scene_state,
        "create_primitive": _handle_create_primitive,
        "import_blend": _handle_import_blend,
        "select_object": _handle_select_object,
        "delete_selected": _handle_delete_selected,
        "export_glb": _handle_export_glb,
        "generate_manifest": _handle_generate_manifest,
        "extract_markers": _handle_extract_markers,
    }

    handler = handlers.get(method)
    if handler is None:
        raise ValueError(f"Unsupported method: {method}")
    return handler(params)


def _handle_ping(_params: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "addon": "gamify_blender_mcp",
        "blender_version": ".".join(str(part) for part in bpy.app.version[:3]),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _handle_get_scene_state(params: dict[str, Any]) -> dict[str, Any]:
    include_transforms = bool(params.get("include_transforms", True))
    objects: list[dict[str, Any]] = []
    for obj in bpy.context.scene.objects:
        payload: dict[str, Any] = {
            "name": obj.name,
            "type": obj.type,
        }
        if include_transforms:
            payload["location"] = [round(float(v), 6) for v in obj.location]
            payload["rotation"] = [round(float(v), 6) for v in obj.rotation_euler]
            payload["scale"] = [round(float(v), 6) for v in obj.scale]
            payload["dimensions"] = [round(float(v), 6) for v in obj.dimensions]
        objects.append(payload)

    return {
        "count": len(objects),
        "objects": objects,
    }


def _handle_create_primitive(params: dict[str, Any]) -> dict[str, Any]:
    primitive_type = str(params.get("type", "CUBE")).upper()
    name = str(params.get("name") or "")
    location = _vector3(params.get("location"), default=(0.0, 0.0, 0.0))
    size = float(params.get("size", 1.0))

    before = {obj.name for obj in bpy.context.scene.objects}

    if primitive_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    elif primitive_type == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size / 2.0, location=location)
    elif primitive_type == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(radius=size / 2.0, depth=size, location=location)
    elif primitive_type == "EMPTY":
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    else:
        raise ValueError(f"Unsupported primitive type: {primitive_type}")

    created = _latest_created_object(before)
    if created is None:
        raise RuntimeError("Failed to create object")

    if name:
        created.name = name

    return {
        "object_name": created.name,
        "type": created.type,
    }


def _handle_import_blend(params: dict[str, Any]) -> dict[str, Any]:
    filepath_raw = params.get("filepath")
    object_name_raw = params.get("object_name")
    if not isinstance(filepath_raw, str) or not filepath_raw:
        raise ValueError("'filepath' is required")
    if not isinstance(object_name_raw, str) or not object_name_raw:
        raise ValueError("'object_name' is required")

    filepath = Path(filepath_raw)
    if not filepath.is_absolute():
        filepath = utils.get_repo_root() / filepath
    if not filepath.exists():
        raise FileNotFoundError(f"Blend file not found: {filepath}")

    with bpy.data.libraries.load(str(filepath), link=False) as (data_from, data_to):
        if object_name_raw not in data_from.objects:
            raise ValueError(f"Object '{object_name_raw}' not found in {filepath}")
        data_to.objects = [object_name_raw]

    imported: list[str] = []
    for obj in data_to.objects:
        if not isinstance(obj, bpy.types.Object):
            continue
        bpy.context.scene.collection.objects.link(obj)
        imported.append(str(getattr(obj, "name", object_name_raw)))

    return {"imported": imported}


def _handle_select_object(params: dict[str, Any]) -> dict[str, Any]:
    name_raw = params.get("name")
    if not isinstance(name_raw, str) or not name_raw:
        raise ValueError("'name' is required")

    bpy.ops.object.select_all(action="DESELECT")
    obj = bpy.data.objects.get(name_raw)
    if obj is None:
        return {"selected": False}

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return {"selected": True, "name": obj.name}


def _handle_delete_selected(_params: dict[str, Any]) -> dict[str, Any]:
    selected = [obj.name for obj in bpy.context.selected_objects]
    if selected:
        bpy.ops.object.delete(use_global=False)
    return {"deleted": selected}


def _handle_export_glb(params: dict[str, Any]) -> dict[str, Any]:
    output_path = _resolve_output_path(params)
    _require_approval_if_requested(params, f"Export GLB to {output_path.name}?")
    utils.export_scene_glb(output_path, include_lights=bool(params.get("include_lights", False)))
    return {"path": str(output_path), "success": True}


def _handle_generate_manifest(params: dict[str, Any]) -> dict[str, Any]:
    output_dir_raw = params.get("output_dir")
    category = params.get("category")
    if category is not None and not isinstance(category, str):
        raise ValueError("'category' must be a string when provided")

    _require_approval_if_requested(params, "Generate asset manifest?")

    manifest_data = utils.compute_manifest_data(category=category)
    manifest_path = manifest_data["path"]
    if output_dir_raw is not None:
        if not isinstance(output_dir_raw, str):
            raise ValueError("'output_dir' must be a string")
        output_dir = Path(output_dir_raw)
        if not output_dir.is_absolute():
            output_dir = utils.get_repo_root() / output_dir
        manifest_path = output_dir / "manifest.json"

    utils.write_json(manifest_path, manifest_data["payload"])
    return {"manifest_path": str(manifest_path)}


def _handle_extract_markers(params: dict[str, Any]) -> dict[str, Any]:
    blend_path = Path(bpy.data.filepath)
    if not blend_path.suffix == ".blend":
        raise RuntimeError("Open a saved .blend file before extracting markers")

    output_raw = params.get("output_path")
    if output_raw is None:
        output_path = blend_path.parent / "markers.json"
    else:
        if not isinstance(output_raw, str):
            raise ValueError("'output_path' must be a string")
        output_path = Path(output_raw)
        if not output_path.is_absolute():
            output_path = utils.get_repo_root() / output_path

    world_id = utils.normalize_marker_id(blend_path.stem)
    markers = []
    for obj in bpy.context.scene.objects:
        if obj.type != "EMPTY":
            continue
        marker_id = utils.normalize_marker_id(obj.name)
        markers.append(
            {
                "marker_id": marker_id,
                "marker_type": utils.marker_type(marker_id),
                "position": [round(float(v), 6) for v in obj.location],
                "rotation": [round(float(v), 6) for v in obj.rotation_euler],
                "properties": {},
            }
        )

    payload = {
        "schema_version": "1.0",
        "world_id": world_id,
        "markers": markers,
    }
    utils.write_json(output_path, payload)
    return {"markers_path": str(output_path), "count": len(markers)}


def _resolve_output_path(params: dict[str, Any]) -> Path:
    output_raw = params.get("output_path")
    if output_raw is None:
        return utils.resolve_asset_export_path()
    if not isinstance(output_raw, str):
        raise ValueError("'output_path' must be a string")
    output_path = Path(output_raw)
    if not output_path.is_absolute():
        output_path = utils.get_repo_root() / output_path
    return output_path


def _require_approval_if_requested(params: dict[str, Any], message: str) -> None:
    if bool(params.get("human_approval", False)):
        approved = socket_server.request_approval(message=message)
        if not approved:
            raise RuntimeError("Operation rejected or approval timed out")


def _vector3(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("Expected 3-item vector")
    return (float(value[0]), float(value[1]), float(value[2]))


def _latest_created_object(before_names: set[str]) -> bpy.types.Object | None:
    candidates = [obj for obj in bpy.context.scene.objects if obj.name not in before_names]
    if not candidates:
        return None
    return candidates[-1]
