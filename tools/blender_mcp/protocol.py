"""Protocol helpers for the Gamify Blender MCP server."""

from __future__ import annotations

from typing import Any

SERVER_INFO = {
    "name": "gamify-blender-mcp",
    "version": "0.1.0",
}

PROTOCOL_VERSION = "2024-11-05"


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "ping",
            "description": "Check Blender MCP bridge health.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_scene_state",
            "description": "List objects in current Blender scene.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_transforms": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "create_primitive",
            "description": "Create a primitive object in the active scene.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["CUBE", "SPHERE", "CYLINDER", "EMPTY"]},
                    "name": {"type": "string"},
                    "location": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                    "size": {"type": "number"},
                },
                "required": ["type"],
                "additionalProperties": False,
            },
        },
        {
            "name": "import_blend",
            "description": "Append one object from another .blend file.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "object_name": {"type": "string"},
                },
                "required": ["filepath", "object_name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "select_object",
            "description": "Select a scene object by name.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "delete_selected",
            "description": "Delete currently selected objects.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "export_glb",
            "description": "Export current scene as GLB.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "output_path": {"type": "string"},
                    "include_lights": {"type": "boolean"},
                    "human_approval": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "generate_manifest",
            "description": "Generate asset manifest JSON for current blend.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "output_dir": {"type": "string"},
                    "category": {"type": "string"},
                    "human_approval": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "extract_markers",
            "description": "Extract EMPTY objects to markers.json.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "output_path": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    ]
