# Blogo_bambu_config

# Blogo – Autonomous 3D Print Preparation Engine (Bambu Lab A1)

Engineering package and automation engine designed for Bambu Lab 3D printers (Target: **Bambu Lab A1**, 0.4mm nozzle).

---

## 📁 Project Directory Structure

```
3dMOdel_agent/
│
├── printmate/                   # Modular Python Architecture Subsystems
│   ├── core/                    # Config, data models (ModelInfo, SlicerProfile), exceptions
│   ├── geometry/                # Safe loading, dimensions, watertight validation, mesh repair
│   ├── intelligence/            # Scale classification and geometric risk assessment
│   ├── splitting/               # Watertight planar mesh bisecting and waistline contour analysis
│   ├── connectors/              # Male dowel pins, female sockets, and Blender headless bridge
│   ├── optimization/            # Material profiles (PLA Basic/Matte/Silk, PETG) and strategies
│   ├── slicer/                  # Bambu Studio .3mf packaging, config injection & bridge
│   ├── workflow/                # State machine lifecycle and pipeline orchestrator
│   └── reporting/               # Diagnostic ASCII console and markdown reports
│
├── tests/                       # Automated Regression Test Suite (19 Tests, 100% Passing)
│   ├── test_geometry.py         # Mesh loading, bounding boxes, build volume fit & validation
│   ├── test_splitting.py        # Planar bisecting, watertight caps, dowel pin & socket geometry
│   ├── test_3mf.py              # 3MF zip structure, parameter injection & slicer validation
│   └── test_regression.py       # Backward-compatible CLI and end-to-end execution
│
├── models/                      # 3D Model Meshes (.stl)
│   ├── raw/                     # Original master mesh (single_color.stl)
│   └── split_parts/             # Split components (Ayyappan Base, Idol, with Male/Female locks)
│
├── outputs/                     # Slicer Projects & Machine Code
│   ├── projects_3mf/            # Verified Bambu Studio .3mf projects (Single & Split scenes)
│   └── gcode/                   # Production-tested G-code files
│
├── docs/                        # Technical Documentation & Master Guides
│   ├── guides/                  # Bambu Studio master KB, showroom HD guide, stringing guide
│   └── reports/                 # Phase 0 implementation report, full state audit
│
├── scripts/                     # Standalone automation helpers (create_dowel_lock.py)
├── _backup_phase0/              # Initial safe backup of prototype scripts
│
├── print_pilot.py               # Main Backward-Compatible CLI Automation Entry Point
└── README.md                    # Project Index & Architecture Guide
```

---

## 🚀 Quick Start

### 1. Run Automated Test Suite
Verify that all 19 regression tests pass:
```powershell
python -m unittest discover tests -v
```

### 2. Run PrintPilot CLI
Generate a safe, zero-breakage Bambu Studio project for your model:
```powershell
# Analyze and package default model (55mm miniature height, safe tree supports)
python print_pilot.py --height 55.0

# Package in support-free split mode with silk PLA tuning
python print_pilot.py --model models/raw/single_color.stl --mode split --filament pla_silk

# Package and launch directly into Bambu Studio
python print_pilot.py --height 55.0 --launch
```

---

## 🛡️ Critical Bambu Lab A1 Safe Overrides
- **Layer Height:** `0.12 mm` (Ultra-fine detail)
- **Wall Loops:** `3` (Reinforced wrist and delicate finger joints)
- **Sparse Infill:** `15% Gyroid` (Uniform strength, zero nozzle dragging)
- **Safe Support Air-Gap:** `Z = 0.24 mm`, `XY = 0.60 mm` (Prevents support fusion on miniature hands)
- **Wall Generator:** `Arachne` (Adaptive thin-wall extrusion)

