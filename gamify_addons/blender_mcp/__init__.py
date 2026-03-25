"""Gamify Blender MCP addon entrypoint."""

from __future__ import annotations

import bpy

from . import socket_server

bl_info = {
    "name": "Gamify Blender MCP",
    "author": "Gamify",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Gamify",
    "description": "Expose Blender scene operations for Gamify MCP orchestration",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}


class GAMIFY_OT_mcp_start_server(bpy.types.Operator):
    """Start MCP socket server."""

    bl_idname = "gamify.mcp_start_server"
    bl_label = "Start MCP Server"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        socket_server.start_server()
        self.report({"INFO"}, "Gamify MCP server started")
        return {"FINISHED"}


class GAMIFY_OT_mcp_stop_server(bpy.types.Operator):
    """Stop MCP socket server."""

    bl_idname = "gamify.mcp_stop_server"
    bl_label = "Stop MCP Server"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        socket_server.stop_server()
        self.report({"INFO"}, "Gamify MCP server stopped")
        return {"FINISHED"}


class GAMIFY_OT_mcp_approve(bpy.types.Operator):
    """Approve the active MCP approval request."""

    bl_idname = "gamify.mcp_approve"
    bl_label = "Approve"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        if socket_server.resolve_approval(True):
            self.report({"INFO"}, "Approval marked approved")
        else:
            self.report({"WARNING"}, "No pending approval request")
        return {"FINISHED"}


class GAMIFY_OT_mcp_reject(bpy.types.Operator):
    """Reject the active MCP approval request."""

    bl_idname = "gamify.mcp_reject"
    bl_label = "Reject"

    def execute(self, _context: bpy.types.Context) -> set[str]:
        if socket_server.resolve_approval(False):
            self.report({"INFO"}, "Approval marked rejected")
        else:
            self.report({"WARNING"}, "No pending approval request")
        return {"FINISHED"}


class GAMIFY_PT_mcp_panel(bpy.types.Panel):
    """Sidebar panel for the Gamify MCP addon."""

    bl_label = "Blender MCP"
    bl_idname = "GAMIFY_PT_mcp_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gamify"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout

        status = socket_server.get_status()
        row = layout.row()
        row.label(text=f"Server: {'Running' if status['running'] else 'Stopped'}")
        row = layout.row()
        row.label(text=f"Port: {status['port']}")

        if status["running"]:
            layout.operator(GAMIFY_OT_mcp_stop_server.bl_idname, icon="CANCEL")
        else:
            layout.operator(GAMIFY_OT_mcp_start_server.bl_idname, icon="PLAY")

        layout.separator()
        layout.label(text=f"Last Method: {status['last_method'] or '-'}")

        approval = status["approval"]
        layout.separator()
        layout.label(text="Human Approval")
        layout.label(text=f"State: {approval['status']}")
        if approval["status"] == "pending":
            layout.label(text=approval["message"][:64])
            row = layout.row(align=True)
            row.operator(GAMIFY_OT_mcp_approve.bl_idname, icon="CHECKMARK")
            row.operator(GAMIFY_OT_mcp_reject.bl_idname, icon="X")


CLASSES = (
    GAMIFY_OT_mcp_start_server,
    GAMIFY_OT_mcp_stop_server,
    GAMIFY_OT_mcp_approve,
    GAMIFY_OT_mcp_reject,
    GAMIFY_PT_mcp_panel,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    socket_server.stop_server()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
