#!/usr/bin/env python3
"""Minimal MCP stdio server bridging to Blender addon socket server."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

if __package__:
    from .blender_client import BlenderClient
    from .protocol import PROTOCOL_VERSION, SERVER_INFO, tool_definitions
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.blender_mcp.blender_client import BlenderClient
    from tools.blender_mcp.protocol import PROTOCOL_VERSION, SERVER_INFO, tool_definitions


def _send(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def _error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def _result_response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "result": result,
    }


def _handle_initialize(message_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    _ = params
    return _result_response(
        message_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {
                "tools": {},
            },
        },
    )


def _handle_tools_list(message_id: Any) -> dict[str, Any]:
    return _result_response(message_id, {"tools": tool_definitions()})


def _handle_tools_call(message_id: Any, params: dict[str, Any], client: BlenderClient) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}

    if not isinstance(name, str) or not name:
        return _error_response(message_id, -32602, "tools/call requires non-empty string 'name'")
    if not isinstance(arguments, dict):
        return _error_response(message_id, -32602, "tools/call 'arguments' must be an object")

    try:
        result = client.call(method=name, params=arguments)
    except Exception as exc:  # noqa: BLE001
        return _error_response(message_id, -32000, f"Blender call failed: {exc}")

    return _result_response(
        message_id,
        {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2),
                }
            ],
            "isError": False,
        },
    )


def main() -> int:
    client = BlenderClient()
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue

        try:
            message = json.loads(text)
        except json.JSONDecodeError:
            _send(_error_response(None, -32700, "Parse error"))
            continue

        message_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}

        if not isinstance(method, str):
            _send(_error_response(message_id, -32600, "Invalid Request: missing method"))
            continue
        if not isinstance(params, dict):
            _send(_error_response(message_id, -32602, "Invalid params"))
            continue

        try:
            if method == "initialize":
                _send(_handle_initialize(message_id, params))
            elif method == "tools/list":
                _send(_handle_tools_list(message_id))
            elif method == "tools/call":
                _send(_handle_tools_call(message_id, params, client))
            elif method == "notifications/initialized":
                continue
            else:
                _send(_error_response(message_id, -32601, f"Method not found: {method}"))
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            _send(_error_response(message_id, -32001, f"Internal server error: {exc}"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
