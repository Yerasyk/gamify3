# Blender + Godot Long-Term Production Workflow
## WSL Implementation Plan

**Working Directory:** `/mnt/c/dev/gamify3` (Windows: `C:\dev\gamify3`)  
**Environment:** WSL2 + Windows GUI tools  
**Target Versions:**
- Blender: 4.5 LTS or newer (currently on your system)
- Godot: 4.6.1-stable
- Python: 3.10+

---

## Quick Start

```bash
# SSH into WSL
wsl

# Navigate to project
cd /mnt/c/dev/gamify3

# (Future) activate venv
source venv/bin/activate

# Start working on current task
```

---

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (planner)                           │
│  Coordinates subagents, validates artifacts, tracks state           │
└─────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│blender_asset │ │blender_world │ │godot_gameplay│ │validator_build│
│              │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                    Artifact Exchange
                (GLB + JSON manifests)
```

### File Ownership

| Subagent | Owns | Does NOT Own |
|----------|------|--------------|
| `blender_asset` | `blender/assets/`, `exports/assets/` | Worlds, gameplay logic |
| `blender_world` | `blender/worlds/`, `exports/worlds/` | Individual assets, runtime code |
| `godot_gameplay` | `godot/scenes/`, `godot/scripts/` | Source Blender files, export tools |
| `validator_build` | `validation/`, `test/`, `reports/` | Asset/world files, gameplay code |
| `planner` | `.opencode/`, `tools/`, orchestration | Specific asset/world/game files |

---

## Repository Structure

```
gamify3/
├── .opencode/
│   └── agents/
│       ├── planner.md
│       ├── blender_asset.md
│       ├── blender_world.md
│       ├── godot_gameplay.md
│       └── validator_build.md
│
├── blender/
│   ├── assets/
│   │   ├── props/
│   │   ├── characters/
│   │   ├── modular/
│   │   └── materials/
│   ├── worlds/
│   │   └── templates/
│   └── scripts/
│       ├── asset_tools/
│       └── world_tools/
│
├── exports/
│   ├── assets/
│   └── worlds/
│
├── godot/
│   ├── project.godot
│   ├── scenes/
│   ├── scripts/
│   ├── resources/
│   └── autoload/
│
├── validation/
│   ├── schemas/
│   ├── scripts/
│   ├── reports/
│   └── ci/
│
├── test/
│   ├── blender/
│   └── godot/
│
├── tools/
│   ├── blender_cli.py
│   ├── godot_cli.py
│   └── manifest_tools.py
│
├── docs/
│   ├── architecture.md
│   ├── conventions.md
│   └── troubleshooting.md
│
├── PLAN.md (this file)
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Cross-Platform Workflow

### Where Tools Live

| Tool | Location | Runs On | Invoked By |
|------|----------|---------|-----------|
| Blender export scripts | `blender/scripts/` | Windows Blender (you run) | You manually in Blender, or I script calls |
| Godot scene files | `godot/` | Windows Godot (you run) | You in editor, or headless tests |
| Python validators | `validation/scripts/`, `tools/` | WSL Python | OpenCode in WSL |
| Git operations | Shared filesystem | WSL | OpenCode in WSL |

### The Loop

```
1. [You] Open Blender on Windows → C:\dev\gamify3\blender\assets\props\crate.blend
2. [You] Model/export asset using Blender UI or run export script
3. [OpenCode/WSL] Validates exported GLB + generates manifest
4. [You] Open Godot on Windows → C:\dev\gamify3\godot\
5. [You] Import GLB scenes, create gameplay logic
6. [OpenCode/WSL] Runs validators, checks dependencies
7. [You] Test in Godot play mode
8. [You] Commit to git (OpenCode can help with messages)
```

---

## Phase 1: Foundation (Days 1-2)

### Day 1: Repository Setup & Directory Structure

**Tasks:**
- [ ] Create directory structure (use bash/mkdir)
- [ ] Create `.gitignore` (Blender, Godot, Python temp files)
- [ ] Set up `pyproject.toml` with dependencies
- [ ] Create placeholder agent instruction files in `.opencode/agents/`
- [ ] Document naming conventions in `docs/conventions.md`

**Commands:**
```bash
cd /mnt/c/dev/gamify3

# Create structure
mkdir -p blender/assets/{props,characters,modular,materials}
mkdir -p blender/worlds/templates
mkdir -p blender/scripts/{asset_tools,world_tools}
mkdir -p exports/{assets,worlds}
mkdir -p godot/{scenes/{levels,entities},scripts,resources,autoload}
mkdir -p validation/{schemas,scripts,reports,ci}
mkdir -p test/{blender,godot}
mkdir -p tools
mkdir -p docs
mkdir -p .opencode/agents
```

**Files to create:**
- `.gitignore` — standard Python + Blender + Godot patterns
- `pyproject.toml` — project metadata, dependencies (jsonschema, pyyaml, etc.)
- `requirements.txt` — pip freeze output
- `docs/conventions.md` — naming, file structure rules
- `.opencode/agents/planner.md` — agent instructions (basic for now)

### Day 2: Python Tooling & JSON Schemas

**Tasks:**
- [ ] Create `tools/manifest_tools.py` — shared utilities for JSON handling
- [ ] Create `validation/schemas/asset_manifest.schema.json`
- [ ] Create `validation/schemas/world_manifest.schema.json`
- [ ] Create `validation/schemas/marker.schema.json`
- [ ] Create `validation/scripts/validate_manifests.py`
- [ ] Create `.gitignore` entries

**What you'll do in Blender/Godot:** Nothing yet, just setup.

**Verification:** 
```bash
python validation/scripts/validate_manifests.py --help
```

---

## Phase 2: First Asset Export (Days 3-5)

### Day 3: Blender Scripts Foundation

**In Windows Blender:**
- [ ] Create `blender/assets/props/crate_wooden.blend`
- [ ] Model: simple 1x1x1 unit cube
- [ ] Add material (basic color or texture)
- [ ] Save and close

**In WSL:**
- [ ] Create `blender/scripts/asset_tools/export_glb.py`
  - Headless script: open `.blend`, export to GLB
  - Set scale, origin, export settings deterministically
- [ ] Create `blender/scripts/asset_tools/generate_manifest.py`
  - Read GLB metadata, create `manifest.json`
- [ ] Create `tools/blender_cli.py` — wrapper to invoke Blender headless

**Verification:**
```bash
python tools/blender_cli.py \
  --blend blender/assets/props/crate_wooden.blend \
  --script blender/scripts/asset_tools/export_glb.py

# Output should be: exports/assets/props/crate_wooden/crate_wooden.glb
```

### Day 4: Asset Manifest & Validation

**In WSL:**
- [ ] Run `generate_manifest.py` on exported crate
- [ ] Verify `exports/assets/props/crate_wooden/manifest.json` created
- [ ] Run `validate_manifests.py` to check schema

**Manifest contract (example):**
```json
{
  "schema_version": "1.0",
  "asset_id": "prop_crate_wooden",
  "asset_type": "prop",
  "source_file": "blender/assets/props/crate_wooden.blend",
  "exported_glb": "exports/assets/props/crate_wooden/crate_wooden.glb",
  "export_timestamp": "2026-03-19T10:00:00Z",
  "blender_version": "4.5.0",
  "dimensions": { "x": 1.0, "y": 1.0, "z": 1.0 },
  "origin": "center_bottom",
  "custom_properties": {}
}
```

### Day 5: World Assembly (Manual, then Script)

**In Windows Blender:**
- [ ] Create `blender/worlds/templates/empty_world.blend` — empty scene, good defaults
- [ ] Create `blender/worlds/level_01/level_01.blend`
- [ ] Link/instance crate asset into world
- [ ] Add empty object "spawn_player" at origin
- [ ] Save

**In WSL:**
- [ ] Create `blender/scripts/world_tools/extract_markers.py`
  - Parse empties from `.blend`, write to `markers.json`
- [ ] Create `blender/scripts/world_tools/export_world_glb.py`
  - Export world GLB with linked assets
  - Generate world manifest

**Verification:**
```bash
python tools/blender_cli.py \
  --blend blender/worlds/level_01/level_01.blend \
  --script blender/scripts/world_tools/extract_markers.py

# Output: blender/worlds/level_01/markers.json
```

**Marker format (example):**
```json
{
  "schema_version": "1.0",
  "world_id": "level_01",
  "markers": [
    {
      "marker_id": "spawn_player",
      "marker_type": "spawn",
      "position": [0, 0, 0],
      "rotation": [0, 0, 0],
      "properties": { "entity": "player" }
    }
  ]
}
```

---

## Phase 3: Godot Foundation (Days 6-8)

### Day 6: Godot Project Setup & GLB Import

**In Windows Godot:**
- [ ] Create `godot/project.godot`
- [ ] Import `exports/worlds/level_01/level_01.glb` manually
  - Right-click → Import
  - Godot auto-creates scene
- [ ] Create `scenes/levels/level_01.tscn` (inherited from imported scene)
- [ ] Add basic 3D camera
- [ ] Save

**In WSL:**
- [ ] Create `tools/godot_cli.py` — wrapper to invoke Godot headless

### Day 7: Player Controller & Marker Loading

**In Windows Godot:**
- [ ] Create `scenes/entities/player.tscn`
  - CharacterBody3D node
  - Capsule collision shape
  - Camera3D child
- [ ] Create `scripts/player_controller.gd`
  - Basic WASD movement (first-person)
  - Mouse look

**In Windows Godot:**
- [ ] Create `scripts/marker_loader.gd`
  - Parse `markers.json`
  - At game start, read markers
  - Spawn player at `spawn_player` position

**In WSL (documentation):**
- [ ] Document the marker→player spawn flow

### Day 8: Playable Loop

**In Windows Godot:**
- [ ] Create `scenes/main.tscn`
  - Load `level_01.tscn`
  - Call `marker_loader.gd` at start
- [ ] Play: walk around crate with WASD + mouse look
- [ ] Fix any scale/rotation issues

**In WSL:**
- [ ] Create basic validation that checks:
  - GLB files exist
  - Manifests are valid JSON Schema
  - Markers file is valid

---

## Phase 4: Validation & Documentation (Days 9-10)

**In WSL:**
- [ ] Create `validation/scripts/validate_all.py`
  - Run all validators in one command
  - Generate `validation/reports/latest_report.json`
- [ ] Create `validation/ci/simple_check.sh` — basic CI hook
- [ ] Write `docs/architecture.md` — overview of system
- [ ] Write `docs/conventions.md` — naming, file structure rules
- [ ] Write `docs/troubleshooting.md` — common issues

**In Git:**
- [ ] Tag `v0.1.0-alpha`
- [ ] Commit message: "Initial vertical slice: asset → world → Godot playable loop"

---

## Artifact Contracts

### Asset Manifest Schema
Located: `validation/schemas/asset_manifest.schema.json`

Required fields:
- `schema_version` (e.g., "1.0")
- `asset_id` (kebab-case, unique)
- `asset_type` ("prop", "character", "modular", "material")
- `source_file` (path to `.blend`)
- `exported_glb` (path to exported `.glb`)
- `export_timestamp` (ISO 8601)
- `blender_version` (X.Y.Z)
- `dimensions` (x, y, z in meters)
- `origin` ("center_bottom", "center_center", "corner")

### World Manifest Schema
Located: `validation/schemas/world_manifest.schema.json`

Required fields:
- `schema_version`
- `world_id` (kebab-case, unique)
- `source_file`
- `exported_glb`
- `markers_file` (path to `markers.json`)
- `export_timestamp`
- `asset_dependencies` (array of asset_id + manifest paths)

### Marker Schema
Located: `validation/schemas/marker.schema.json`

Structure:
```json
{
  "marker_id": "unique_id",
  "marker_type": "spawn|trigger|waypoint|light|sound|custom",
  "position": [x, y, z],
  "rotation": [pitch, yaw, roll],
  "properties": { "key": "value" }
}
```

---

## Naming Conventions

### Files
- Blender files: `snake_case.blend`
- Godot scenes: `PascalCase.tscn`
- Godot scripts: `snake_case.gd`
- Python scripts: `snake_case.py`
- JSON manifests: `manifest.json` (always this name in versioned dirs)

### Identifiers
- Asset IDs: `category_name` (e.g., `prop_crate_wooden`)
- World IDs: `level_NN` (e.g., `level_01`)
- Marker IDs: `marker_type_name` (e.g., `spawn_player`, `trigger_door_01`)

### Directories
- Exports: `exports/<type>/<category>/<id>/`
- Blender sources: `blender/<type>/<category>/<id>.<blend>`

---

## Cross-Platform Commands

### Running Python validators in WSL
```bash
cd /mnt/c/dev/gamify3
source venv/bin/activate  # if you create venv
python validation/scripts/validate_manifests.py
```

### Running headless Blender (future)
```bash
python tools/blender_cli.py \
  --blend blender/assets/props/my_asset.blend \
  --script blender/scripts/asset_tools/export_glb.py
```

### Opening files in Windows from WSL
```bash
# Open in Blender (example)
blender "C:\dev\gamify3\blender\assets\props\crate_wooden.blend"
# or via WSL path
blender /mnt/c/dev/gamify3/blender/assets/props/crate_wooden.blend
```

---

## Important Notes

### No WSL Blender/Godot Required Yet
- Blender and Godot run on Windows for visual work
- Python validation scripts run in WSL
- We'll install Blender/Godot in WSL only if headless automation becomes essential

### Export Paths
All exports go to `exports/` in the repo. Git ignores `.glb` files (add to `.gitignore`).
Source `.blend` files stay in `blender/`.

### Manifest as Source of Truth
Each exported asset/world must have a corresponding `manifest.json`.
The manifest records metadata that `.blend` and `.glb` can't carry (custom properties, dependencies).

### Schema Versioning
All schemas are versioned from day 1. When you change a schema, bump the version number.
Write migration scripts if needed.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Blender API changes | Pin version in manifest, record version during export |
| GLB scale/transform issues | Deterministic export settings, early testing |
| Godot GLB import inconsistency | Test with reference assets, document import settings |
| WSL↔Windows file sync issues | Repo on Windows filesystem, avoid moving files while open |
| Schema drift | Version all schemas, validate strictly |

---

## Next Steps

1. **Right now:** Verify you can navigate to `/mnt/c/dev/gamify3` in WSL
2. **Create new WSL session in that directory**
3. **Start Day 1 tasks:** build directory structure, create `.gitignore`, setup Python
4. **Then:** Day 2 JSON schemas and validators
5. **Then:** Day 3-5 first asset export loop

---

## Git Workflow

```bash
# After each day's work
git add .
git commit -m "Day N: <specific work done>"
git push

# Tag releases
git tag v0.1.0-alpha
```

All changes go to a `main` branch for this solo project (or create `dev` if you prefer).

---

## Questions Before Starting

1. Should I install Blender/Godot in WSL for headless work, or keep it Windows-only?
2. Do you want a Python venv, or bare system Python?
3. Should I create all Day 1 structure files now, or do you want to do it manually?

Answer in next message and we'll begin Day 1 setup.
