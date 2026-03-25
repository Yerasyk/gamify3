"""Socket server hosted inside Blender for MCP commands."""

from __future__ import annotations

import json
import socket
import threading
from typing import Any

HOST = "127.0.0.1"
PORT = 9876

_server_socket: socket.socket | None = None
_server_thread: threading.Thread | None = None
_stop_event = threading.Event()
_status_lock = threading.Lock()
_last_method = ""

_approval_lock = threading.Lock()
_approval_status = "idle"
_approval_message = ""
_approval_event: threading.Event | None = None
_approval_result: bool | None = None


def _set_last_method(method: str) -> None:
    global _last_method
    with _status_lock:
        _last_method = method


def get_status() -> dict[str, Any]:
    with _status_lock:
        running = _server_thread is not None and _server_thread.is_alive()
        last_method = _last_method
    with _approval_lock:
        approval = {
            "status": _approval_status,
            "message": _approval_message,
        }
    return {
        "running": running,
        "host": HOST,
        "port": PORT,
        "last_method": last_method,
        "approval": approval,
    }


def start_server() -> None:
    global _server_thread
    if _server_thread is not None and _server_thread.is_alive():
        return

    _stop_event.clear()
    _server_thread = threading.Thread(target=_serve_forever, name="GamifyMCPServer", daemon=True)
    _server_thread.start()


def stop_server() -> None:
    global _server_socket
    _stop_event.set()
    if _server_socket is not None:
        try:
            _server_socket.close()
        except OSError:
            pass
        _server_socket = None


def resolve_approval(approved: bool) -> bool:
    global _approval_status, _approval_result, _approval_event
    with _approval_lock:
        if _approval_status != "pending" or _approval_event is None:
            return False
        _approval_status = "approved" if approved else "rejected"
        _approval_result = approved
        _approval_event.set()
    return True


def request_approval(message: str, timeout_seconds: float = 300.0) -> bool:
    global _approval_status, _approval_message, _approval_event, _approval_result

    event = threading.Event()
    with _approval_lock:
        if _approval_status == "pending":
            raise RuntimeError("Another approval request is already pending")
        _approval_status = "pending"
        _approval_message = message
        _approval_event = event
        _approval_result = None

    completed = event.wait(timeout=timeout_seconds)
    with _approval_lock:
        if not completed:
            _approval_status = "timeout"
            _approval_message = message
            _approval_event = None
            _approval_result = None
            return False

        approved = bool(_approval_result)
        _approval_message = message
        _approval_event = None
        _approval_result = None
        return approved


def _serve_forever() -> None:
    global _server_socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(8)
    server.settimeout(0.5)
    _server_socket = server

    try:
        while not _stop_event.is_set():
            try:
                conn, _addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                _handle_connection(conn)
    finally:
        try:
            server.close()
        except OSError:
            pass
        _server_socket = None


def _handle_connection(conn: socket.socket) -> None:
    conn.settimeout(5.0)
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk

    if not data:
        return

    raw = data.decode("utf-8", errors="replace").strip()
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        response = {"ok": False, "error": f"Invalid JSON: {exc}"}
        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
        return

    method = request.get("method")
    if isinstance(method, str):
        _set_last_method(method)

    try:
        from .handlers import handle_request

        result = handle_request(request)
        response = {"ok": True, "result": result}
    except Exception as exc:  # noqa: BLE001
        response = {"ok": False, "error": str(exc)}

    conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
