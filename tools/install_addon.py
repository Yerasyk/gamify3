#!/usr/bin/env python3
"""Install Gamify Blender MCP addon into Blender user addons directory."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Gamify Blender MCP addon")
    parser.add_argument(
        "--blender-addons-dir",
        type=Path,
        default=None,
        help="Override Blender user addons directory",
    )
    parser.add_argument(
        "--blender-version",
        default="4.5",
        help="Blender major.minor version used for default addon path",
    )
    return parser.parse_args()


def _is_wsl() -> bool:
    return sys.platform.startswith("linux") and (
        "WSL_DISTRO_NAME" in os.environ or "WSL_INTEROP" in os.environ
    )


def _wsl_windows_appdata() -> Path | None:
    if not _is_wsl():
        return None

    users_root = Path("/mnt/c/Users")
    if not users_root.exists():
        return None

    ignored = {"All Users", "Default", "Default User", "Public", "defaultuser0"}
    candidates: list[Path] = []
    for child in sorted(users_root.iterdir()):
        if not child.is_dir() or child.name in ignored:
            continue
        appdata = child / "AppData" / "Roaming"
        if appdata.exists():
            candidates.append(appdata)

    if not candidates:
        return None

    with_blender = [
        path
        for path in candidates
        if (path / "Blender Foundation" / "Blender").exists() or (path / "Blender").exists()
    ]
    if with_blender:
        return with_blender[0]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _blender_root_from_roaming(roaming_dir: Path) -> Path:
    preferred = roaming_dir / "Blender Foundation" / "Blender"
    legacy = roaming_dir / "Blender"
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return preferred


def default_addons_dir(blender_version: str) -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return _blender_root_from_roaming(Path(appdata)) / blender_version / "scripts" / "addons"

    wsl_appdata = _wsl_windows_appdata()
    if wsl_appdata is not None:
        return _blender_root_from_roaming(wsl_appdata) / blender_version / "scripts" / "addons"

    home = Path.home()
    if sys.platform == "darwin":
        return (
            home
            / "Library"
            / "Application Support"
            / "Blender"
            / blender_version
            / "scripts"
            / "addons"
        )
    return home / ".config" / "blender" / blender_version / "scripts" / "addons"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "gamify_addons" / "blender_mcp"
    if not source.exists():
        raise SystemExit(f"Addon source directory not found: {source}")

    destination_root = args.blender_addons_dir or default_addons_dir(args.blender_version)
    destination = destination_root / "blender_mcp"
    destination_root.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)

    print(f"Installed addon to: {destination}")
    print("Open Blender > Preferences > Add-ons, then enable 'Gamify Blender MCP'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
