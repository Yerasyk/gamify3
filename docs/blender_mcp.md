# Blender MCP

This phase adds a Blender addon plus a local MCP stdio server so an orchestrator can drive Blender with a human-in-the-loop option.

## Components

- Blender addon: `gamify_addons/blender_mcp/`
- MCP stdio server: `tools/blender_mcp/server.py`
- Addon installer script: `tools/install_addon.py`

## Install Addon

Auto-install (recommended):

```bash
python3 tools/install_addon.py --blender-version 4.5
```

Then in Blender:

1. Open `Edit > Preferences > Add-ons`
2. Search for `Gamify Blender MCP`
3. Enable it

Manual install:

1. Copy `gamify_addons/blender_mcp` into Blender addons directory
2. Enable `Gamify Blender MCP` in Preferences

## Blender UI

Panel location: `View3D > Sidebar > Gamify > Blender MCP`

Panel controls:

- `Start MCP Server` / `Stop MCP Server`
- Status display (server, port, last method)
- Human approval actions (`Approve` / `Reject`) when approval is pending

Default socket endpoint: `127.0.0.1:9876`

## Run MCP Server

From repo root:

```bash
python3 tools/blender_mcp/server.py
```

This server accepts MCP stdio JSON-RPC methods and forwards tool calls to the Blender addon server.

If you use OpenCode with this repository, `opencode.json` is configured to auto-start this local MCP server as `blender_mcp`.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "blender_mcp": {
      "type": "local",
      "command": ["python3", "tools/blender_mcp/server.py"],
      "enabled": true
    }
  }
}
```

Note: the OpenCode MCP process starts automatically, but Blender addon socket server still needs to be running in Blender (`Start MCP Server` in the panel).

## Supported MCP Tools

- `ping`
- `get_scene_state`
- `create_primitive`
- `import_blend`
- `select_object`
- `delete_selected`
- `export_glb`
- `generate_manifest`
- `extract_markers`

## Human-in-the-Loop

Use `human_approval: true` on supported write/export operations. The addon sets approval state to `pending`, and the operation waits for explicit approval or rejection in Blender UI.

If approval is rejected or times out, the operation returns an error and does not proceed.
