#!/usr/bin/env python3
"""Run Blender headless scripts in a consistent way."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke Blender with a .blend file and Python script."
    )
    parser.add_argument("--blend", required=True, type=Path, help="Path to .blend file")
    parser.add_argument(
        "--script", required=True, type=Path, help="Path to Blender Python script"
    )
    parser.add_argument(
        "--blender-exe",
        default="blender",
        help="Blender executable (default: blender)",
    )
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Run Blender with UI instead of --background",
    )
    parser.add_argument(
        "--script-arg",
        action="append",
        default=[],
        help="Argument to forward to script; repeat for multiple values",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    blend_path = args.blend.resolve()
    script_path = args.script.resolve()

    command = [args.blender_exe, str(blend_path)]
    if not args.foreground:
        command.append("--background")
    command.extend(["--python", str(script_path)])

    if args.script_arg:
        command.append("--")
        command.extend(args.script_arg)

    print("Running:")
    print(" ".join(command))

    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
