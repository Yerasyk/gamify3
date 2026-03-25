#!/usr/bin/env python3
"""Validate manifest JSON files against project schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator as ActiveValidator
except ImportError:
    from jsonschema import Draft7Validator as ActiveValidator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "validation" / "schemas"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_validator(schema_name: str) -> Any:
    schema_path = SCHEMA_DIR / schema_name
    schema = load_json(schema_path)
    return ActiveValidator(schema)


def collect_targets(root: Path) -> list[Path]:
    manifests = sorted(root.glob("**/manifest.json"))
    markers = sorted(root.glob("**/markers.json"))
    return manifests + markers


def pick_validator(path: Path, payload: dict[str, Any]) -> Any | None:
    if path.name == "markers.json":
        return build_validator("marker.schema.json")

    if path.name != "manifest.json":
        return None

    if "asset_id" in payload:
        return build_validator("asset_manifest.schema.json")

    if "world_id" in payload and "asset_dependencies" in payload:
        return build_validator("world_manifest.schema.json")

    return None


def validate_file(path: Path) -> list[str]:
    try:
        payload = load_json(path)
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON ({exc})"]

    if not isinstance(payload, dict):
        return [f"{path}: expected JSON object as root"]

    validator = pick_validator(path, payload)
    if validator is None:
        return [f"{path}: unable to determine schema type"]

    errors = []
    for err in validator.iter_errors(payload):
        location = ".".join(str(part) for part in err.path) or "<root>"
        errors.append(f"{path}: {location}: {err.message}")
    return sorted(errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate manifest.json and markers.json files against schemas."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Root directory to scan (default: repository root)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = collect_targets(args.root)

    if not targets:
        print("No manifest.json or markers.json files found.")
        return 0

    all_errors: list[str] = []
    for target in targets:
        all_errors.extend(validate_file(target))

    if all_errors:
        print("Validation failed:")
        for line in all_errors:
            print(f"- {line}")
        return 1

    print(f"Validation passed for {len(targets)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
