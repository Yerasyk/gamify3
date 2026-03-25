"""Socket client for talking to Blender addon server."""

from __future__ import annotations

import json
import socket
from typing import Any


class BlenderClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9876, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request = {
            "method": method,
            "params": params or {},
        }
        payload = (json.dumps(request) + "\n").encode("utf-8")

        with socket.create_connection((self.host, self.port), timeout=self.timeout) as conn:
            conn.sendall(payload)
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk

        if not data:
            raise RuntimeError("No response from Blender addon server")

        response = json.loads(data.decode("utf-8", errors="replace").strip())
        if not response.get("ok"):
            message = response.get("error", "Unknown error")
            raise RuntimeError(str(message))

        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("Invalid response payload from Blender addon server")
        return result
