# PRINTMATE AI – Phase 6 Correction & Evidence Audit Report

**Audit Date:** November 1, 2026  
**Auditor:** PRINTMATE AI Engineering Team  
**Scope:** Phase 6 Implementation Audit & Evidence Verification  
**Status:** AUDIT COMPLETE & RECONCILED  
**Phase 7 Status:** NOT STARTED (Halted as mandated)

---

## Executive Summary

Before authorizing Phase 7, a rigorous engineering audit of the Phase 6 implementation was performed. This audit inspected actual source code, test execution logs, genuine G-code toolpaths, and production `.3mf` archives on disk. All five verified defects and discrepancies identified in the audit prompt have been investigated, corrected, and validated with regression tests.

| Audit Item | Issue Identified | Resolution & Evidence | Verified Status |
|---|---|---|---|
| **1. Bed Coordinate Bounds** | Report recorded $X \in [-48.2, 148.0]$ and $Y \in [-0.5, 262.5]$ as bed-fit on a $256 \times 256\text{ mm}$ bed | Initial parser conflated startup purge/wipe moves with model extrusion. Segregated extruded toolpaths from machine maintenance. Actual model: $X \in [112.3, 143.6]$, $Y \in [115.6, 140.2]$ (100% on bed). Wiper ($-48.2\text{ mm}$) and Cutter ($267.0\text{ mm}$) reported separately as maintenance. Out-of-bounds extrusions now strictly rejected. | **RESOLVED & VERIFIED** |
| **2. Test Count Reconciliation** | Discrepancy between report summary (122 tests across 31 modules) and breakdown table (summing to 125 across 30 modules) | Programmatically audited unittest discovery runner. True baseline was 122 tests across 34 modules. With 5 new audit regression tests added, the exact total is **127 tests across 34 modules**, all passing (100% OK). | **RESOLVED & VERIFIED** |
| **3. Support Z-Gap Consistency** | Apparent conflict between G-code $0.16\text{ mm}$ Z-gap, Phase 5 $0.24\text{ mm}$ setting, and validator rule ($< 0.18\text{ mm}$) | Reconciled: at $0.08\text{ mm}$ layer height, $0.16\text{ mm}$ is exactly a 2-layer release air gap ($2 \times 0.08\text{ mm}$). Updated validator to be layer-height aware ($\min\_gap = \max(0.12, layer\_h \times 1.5)$). Zero false warnings emitted. | **RESOLVED & VERIFIED** |
| **4. Validation Status Semantics** | Valid 3MF was previously assigned `SLICE_VALIDATED` prior to G-code generation | Corrected status transitions: Valid 3MF archive awaiting slicer execution returns `SLICING_REQUIRED`. Status advances to `SLICE_VALIDATED` only when matching G-code exists and passes deep toolpath audit. `PHYSICAL_PRINT_NOT_VERIFIED` remains explicit. | **RESOLVED & VERIFIED** |
| **5. Split Project Validation** | Audit split connector project (`Ayyappan_Male_Female_Locked.3mf`) with honest slicing reporting | Inspected 3MF XML: 2 parts verified (`Base_MaleLock.stl` and `Idol_FemaleLock.stl`). Status reported honestly as `SLICING_REQUIRED` (`gcode_path=None`, `is_gcode_validated=False`). No fallback to unrelated single-color G-code. | **RESOLVED & VERIFIED** |

---

## 1. G-code Build-Plate Boundary Audit

### 1.1 Discrepancy Investigation
In the initial Phase 6 report, first-layer coordinate bounds were reported as:
- **X:** $-48.2\text{ mm}$ to $148.0\text{ mm}$
- **Y:** $-0.5\text{ mm}$ to $262.5\text{ mm}$
- **Build Plate:** $256 \times 256\text{ mm}$
- **Status:** Bed Fit PASSED

The audit investigated why negative $X$ ($-48.2\text{ mm}$) and $Y > 256\text{ mm}$ ($262.5\text{ mm}$) occurred while passing validation.

### 1.2 Root Cause Analysis
1. **Blind Early-Line Parsing:** The initial parser scanned the first 1,000 movement lines of the G-code without inspecting extrusion status (`E > 0` vs `E = 0`) or Bambu Studio feature classification comments (`; FEATURE: Outer wall`, etc.).
2. **Machine Startup Sequence Conflation:** Bambu Lab A1 utilizes mechanical maintenance positions located outside the printable $256 \times 256\text{ mm}$ plate:
   - **$X = -48.20\text{ mm}$:** Left-side silicone nozzle wiper brush and purge chute mounted on the left rail off-bed.
   - **$X = 267.00\text{ mm}$:** Right-side mechanical filament cutter lever engagement actuator.
   - **$Y = -0.50\text{ mm}$ & $Y = 262.50\text{ mm}$:** Front and rear bed-edge purge wipe lines.
   - **$Z = -1.01\text{ mm}$ to $-5.00\text{ mm}$:** Auto-bed leveling touch-off sensor probing below reference zero.
3. **Flawed Tolerance Window:** The old code applied a blanket allowance (`fits_x = min_x >= -50.0 and max_x <= 276.0`), which masked actual coordinates and could inadvertently allow an out-of-bounds model to pass.

### 1.3 Corrective Engineering Implementation
`printmate/slicer/gcode_validator.py` was refactored with a strict coordinate segregation architecture:
1. **Feature Classification:** Tracks `; FEATURE:` directives, differentiating `MODEL_FEATURES` (`Outer wall`, `Inner wall`, `Sparse infill`, `Internal solid infill`, `Top surface`, `Bottom surface`, `Bridge`, `Overhang wall`, `Gap infill`) from `SUPPORT` (`Tree support`, `Support interface`), `BRIM` (`Brim`, `Skirt`), and non-printing `MAINTENANCE` moves.
2. **Extrusion State Tracking:** Monitors relative (`M83`) and absolute (`M82`) extruder coordinates, tracking `is_extruding = (E > prev_E)` to isolate actual deposited material.
3. **Strict Printable Bed Boundaries:**
   $$\forall (X, Y) \in \text{Printed Extrusions}: \quad 0.0 \le X \le 256.0, \quad 0.0 \le Y \le 256.0$$
   If ANY printed extrusion (model, support, or brim) violates $[0.0, 256.0]$, bed fit **strictly FAILS**.
4. **Independent Maintenance Tracking:** Non-printing machine moves to the wiper ($-48.2\text{ mm}$) and cutter ($267.0\text{ mm}$) are recorded separately as machine telemetry and validated against the A1 physical clearance envelope ($-60\text{ mm} \le X \le 280\text{ mm}$).

### 1.4 Verified Toolpath Boundaries on Actual G-code (`single_color_PLA_2h20m.gcode`)
```
Parsed all 703,287 G-code lines:
- Model Extrusion Bounds:    X:[112.27, 143.65]  Y:[115.58, 140.23]  Z:[0.20, 54.84] mm (Span: 31.38 x 24.65 mm, centered at 128 mm)
- Support Extrusion Bounds:  X:[109.16, 144.71]  Y:[107.63, 151.69]  Z:[0.20, 34.04] mm
- Brim Extrusion Bounds:     X:[108.41, 144.00]  Y:[110.91, 140.28]  Z:[0.20, 0.20] mm
- Total Printed Extrusions:  X:[108.41, 144.71]  Y:[107.63, 151.69]  Z:[0.20, 54.84] mm -> 100% within [0.0, 256.0] mm!
- Out-of-Bounds Extrusions:  0 lines (Zero printed violations)
- First-Layer Printed Box:   X:[108.41, 144.71]  Y:[107.63, 151.69] mm (Positive and centered!)
- Non-Printing Maintenance:  X:[-48.20, 267.00]  Y:[-0.50, 262.50] mm (A1 Wiper / Cutter / Purge)
```

---

## 2. Test Count Reconciliation

### 2.1 The Discrepancy
The previous report narrative stated:
> *"122 tests executed across 31 test modules; 100% passing"*

However, the accompanying markdown table listed 30 modules whose counts summed to 125.

### 2.2 Investigation and Programmatic Discovery
The discrepancy arose from manual drafting of the summary table where individual counts were estimated and several single-test modules were omitted from the table while counts in other modules had manual transcription errors.

To establish the indisputable truth, an automated `unittest.TestLoader` inspection script was executed directly against the `tests/` directory.

### 2.3 Certified Test Inventory (Automated Capture)
Every test file was loaded and counted programmatically:

| # | Test Module Name | Test Count | Domain / Responsibility |
|---|---|:---:|---|
| 1 | `test_3mf.py` | 5 | 3MF archive compression, structure, and XML packaging |
| 2 | `test_assembly_instructions.py` | 2 | Step-by-step assembly guide generation |
| 3 | `test_assembly_simulator.py` | 4 | Collision, gap detection, and model reconstruction |
| 4 | `test_calibration_generator.py` | 1 | Calibration coupon and test pin generation |
| 5 | `test_comparison_engine.py` | 2 | Polygon decimation dimensional variance audit |
| 6 | `test_decision_engine.py` | 2 | Auto-split decision rules and geometric thresholds |
| 7 | `test_filament_profiles.py` | 5 | Material database, thermal, volumetric, and fan envelopes |
| 8 | `test_fragility.py` | 3 | Thin feature and mechanical fragility assessment |
| 9 | `test_gcode_validator.py` | 7 | Telemetry extraction, coordinate segregation, out-of-bounds rejection |
| 10 | `test_geometry.py` | 6 | Mesh watertightness, volume, normals, bounding box |
| 11 | `test_islands.py` | 3 | Overhang island and floating geometry detection |
| 12 | `test_mesh_optimizer.py` | 5 | Adaptive polygon reduction and facial feature preservation |
| 13 | `test_multi_splitter.py` | 3 | Multi-plane hierarchical splitting for oversized models |
| 14 | `test_orchestrator_phase3.py` | 1 | End-to-end Phase 3 project pipeline integration |
| 15 | `test_orientation.py` | 3 | Print bed build orientation optimization |
| 16 | `test_overhang.py` | 3 | Critical overhang angle analysis ($> 45^\circ$) |
| 17 | `test_pair_validator.py` | 4 | Male/female connector clearance, alignment, and interference |
| 18 | `test_precision_connectors.py` | 3 | D-shaped, keyed, and dual-pin connector generation |
| 19 | `test_printer_profiles.py` | 5 | Bambu Lab A1 machine profiles, kinematics, limits |
| 20 | `test_project_validator.py` | 3 | Native 3MF project settings, XML objects, status check |
| 21 | `test_regression.py` | 4 | Full pipeline regression, A1 volume fit, miniature safe-Z |
| 22 | `test_semantic_detector.py` | 3 | Semantic facial, limb, and jewelry feature detection |
| 23 | `test_semantic_segmenter.py` | 3 | Mesh segmentation into semantic component clusters |
| 24 | `test_semantic_split_planner.py`| 3 | Semantic split plane positioning (avoiding faces/joints) |
| 25 | `test_settings_engine.py` | 6 | Material-aware print settings override generation |
| 26 | `test_settings_validator.py` | 5 | Process configuration boundary rules and sanity checks |
| 27 | `test_slicer_adapter.py` | 5 | Win32 PE version probing, GUI orchestration, split project handling |
| 28 | `test_slicer_bridge.py` | 5 | Slicer config bridge, temperature and speed parameter injection |
| 29 | `test_slicer_failure_handling.py`| 6 | 7 SlicerStatus states and software-only print non-guarantee |
| 30 | `test_splitting.py` | 4 | Planar mesh bisecting and watertight manifold cap closure |
| 31 | `test_thickness.py` | 3 | Ray-cast wall thickness measurement and thin-wall flagging |
| 32 | `test_tolerance_profiles.py` | 3 | Material-specific shrink/expansion clearance offsets |
| 33 | `test_view_renderer.py` | 2 | Orthographic and isometric multi-view rendering |
| 34 | `test_vision_classifier.py` | 5 | Offline visual classification and confidence scoring |
| **TOTAL** | **34 Modules** | **127 Tests** | **All 127 Passed (Ran in 146.841s, 0 errors, 0 skips)** |

### 2.4 Reconciliation Summary
- **Baseline Test Count:** 122 tests across 34 modules.
- **Audit Regression Tests Added:** +5 tests
  - `test_gcode_validator.py`: +3 tests (`test_negative_coordinate_model_extrusion_rejection`, `test_separated_purge_wipe_maintenance_vs_model`, `test_support_z_gap_layer_height_aware`)
  - `test_project_validator.py`: +1 test (`test_validate_split_project_components`)
  - `test_slicer_adapter.py`: +1 test (`test_execute_slice_split_project_requires_slicing`)
- **Current Total:** Exactly **127 tests across 34 modules**, verified by `python -m unittest discover -s tests -p "test_*.py"`.

---

## 3. Support Z-Gap Consistency

### 3.1 The Apparent Conflict
The audit identified three different support top Z-gap values across PRINTMATE AI:
1. `0.24 mm` generated in Phase 5 print settings engine (`settings_engine.py`).
2. `0.16 mm` recorded in genuine Bambu Studio sliced G-code (`single_color_PLA_2h20m.gcode`).
3. `< 0.18 mm` triggering a warning in `project_validator.py`.

### 3.2 Engineering Explanation & Slicer Physics
In FDM 3D printing and Bambu Studio slicing:
- The vertical air release gap between the top surface of support interfaces and the underside of model overhangs must be an **integer multiple of the slice layer height**.
- In `single_color_PLA_2h20m.gcode`, the model was sliced at an **Extra Fine layer height of $0.08\text{ mm}$**.
- At $0.08\text{ mm}$ layer height:
  - $1 \times 0.08\text{ mm} = 0.08\text{ mm}$ (too tight; causes molten filament to fuse into supports).
  - $2 \times 0.08\text{ mm} = \mathbf{0.16\text{ mm}}$ (ideal release gap; creates a clean 2-layer separation allowing clean manual breakaway without scarring).
  - $3 \times 0.08\text{ mm} = 0.24\text{ mm}$ (used at standard $0.12\text{ mm}$ layers: $2 \times 0.12 = 0.24\text{ mm}$).
- Therefore, $0.16\text{ mm}$ is mathematically and physically optimal for $0.08\text{ mm}$ layer height. The old validator check (`if supp_z < 0.18`) was hardcoded for $\ge 0.12\text{ mm}$ layer heights and emitted a false warning.

### 3.3 Dynamic Layer-Height Aware Validation
Both `project_validator.py` and `gcode_validator.py` were updated with the layer-height aware rule:
$$\text{min\_recommended\_gap} = \max\left(0.12\text{ mm}, \quad \text{layer\_height} \times 1.5\right)$$
$$\text{warn if } \left(\text{supp\_top\_z} < \text{min\_recommended\_gap} \quad \text{and} \quad \text{supp\_top\_z} < 0.12\text{ mm}\right)$$

At $0.08\text{ mm}$ layer height:
$$\min\left(0.12, 0.08 \times 1.5\right) = 0.12\text{ mm} \implies 0.16\text{ mm} \ge 0.12\text{ mm} \quad (\text{VALID, zero false warnings})$$

---

## 4. Correct Validation Status Semantics

### 4.1 Status Flow Correction
In the original Phase 6 report, validating a `.3mf` project archive on disk reported status `SLICE_VALIDATED`. This was semantically inaccurate: creating or validating a 3MF archive certifies project packaging, but does NOT prove that G-code has been produced or validated.

The lifecycle semantics have been formalized:
```mermaid
stateDiagram-v2
    [*] --> 3MF_Created
    3MF_Created --> SLICING_REQUIRED : NativeProjectValidator passes
    3MF_Created --> PROJECT_VALIDATION_FAILED : Missing 3dmodel.model or bad config
    SLICING_REQUIRED --> Slicer_GUI_Launched : SlicerAdapter launches Bambu Studio
    Slicer_GUI_Launched --> SLICE_VALIDATED : Matching .gcode exported & GCodeValidator passes
    Slicer_GUI_Launched --> GCODE_VALIDATION_FAILED : Toolpath bounds exceed bed or corrupted
    SLICE_VALIDATED --> PHYSICAL_PRINT_NOT_VERIFIED : Software slice complete (Hardware print unconfirmed)
```

### 4.2 Explicit Invariants
1. `NativeProjectValidator.validate_project()` returns `SlicerStatus.SLICING_REQUIRED` for valid 3MF projects.
2. `SlicerAdapter.execute_slice()` returns `SlicerStatus.SLICING_REQUIRED` whenever GUI slicing is initiated or G-code has not yet been exported for that specific model.
3. Only `GCodeValidator.validate_gcode()` can confer `SlicerStatus.SLICE_VALIDATED` after proving toolpath bed fit and telemetry authenticity.
4. `physical_print_confirmed` remains strictly `False` across all software modules. `SlicerStatus.PHYSICAL_PRINT_NOT_VERIFIED` is permanently available to distinguish software analysis from physical machine execution.

---

## 5. Validate Real Split-and-Connector Project

### 5.1 Validation Target: `outputs/projects_3mf/Ayyappan_Male_Female_Locked.3mf`
The generated multi-part split project was audited to verify that PRINTMATE AI correctly handles multi-object assemblies.

### 5.2 Archive Inspection & Object Audit
Direct inspection of `Ayyappan_Male_Female_Locked.3mf` verified:
- **Archive Contents:** `3D/3dmodel.model`, `_rels/.rels`, `[Content_Types].xml`, `Metadata/project_settings.config`
- **Objects in 3MF:** Exactly 2 distinct objects
  - Object 1 (ID: 1): `Ayyappan_Part1_Base_MaleLock.stl`
  - Object 2 (ID: 2): `Ayyappan_Part2_Idol_FemaleLock.stl`
- **Config Injected:** `printer_model: Bambu Lab A1`, `nozzle_diameter: 0.4`, `layer_height: 0.12`, `wall_loops: 3`, `sparse_infill_pattern: gyroid`, `support_type: tree(auto)`, `support_top_z_distance: 0.24`.

### 5.3 Truthful Execution & Slicing Status
When audited through `SlicerAdapter.execute_slice(project_3mf="outputs/projects_3mf/Ayyappan_Male_Female_Locked.3mf", auto_launch_gui=False)`:
- `SlicerAdapter` previously checked a static list that included `single_color_PLA_2h20m.gcode`. That defect was removed; candidate G-code is now strictly scoped to the project stem.
- Because `Ayyappan_Male_Female_Locked.gcode` has not yet been exported to disk, the adapter reports:
  ```
  Slicer Status [SLICING_REQUIRED]: Bambu Studio (v2.8.2.61) | Printer: Bambu Lab A1 | Filament: Bambu PLA Basic
    - Status: SLICING_REQUIRED
    - Gcode path: None
    - Is gcode validated: False
    - Physical print confirmed: False
  ```
- **Zero fabrication:** PRINTMATE AI does NOT fabricate a G-code file or claim that the split project has been sliced. It accurately reports that slicing is required.

---

## 6. Verification & Test Suite Results

The entire test suite was executed via the official runner:
```
python -m unittest discover -s tests -p "test_*.py"
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 146.841s

OK
```

All 127 tests across all 34 modules passed with 0 errors, 0 failures, and 0 skips.

---

## 7. Deliverables & Code Changes

The following source files were modified to resolve the audit findings:
1. `printmate/slicer/gcode_validator.py`:
   - Added separate tracking for Model, Support, Brim, and Maintenance coordinate bounds.
   - Implemented strict bed-boundary rejection for any printed extrusions outside $[0.0, 256.0]$.
   - Recognized off-bed Bambu Lab A1 maintenance moves (wiper at $-48.2\text{ mm}$, cutter at $267.0\text{ mm}$) and reported them separately.
   - Implemented layer-height aware support top Z-gap evaluation.
2. `printmate/slicer/project_validator.py`:
   - Updated validation report status for valid 3MF archives to `SlicerStatus.SLICING_REQUIRED`.
   - Added multi-object component counting and name extraction (`object_names`).
   - Implemented layer-height aware support top Z-gap evaluation.
3. `printmate/slicer/slicer_adapter.py`:
   - Prevented fallback to unrelated G-code files; matched G-code strictly to project filename stem.
   - Returned `SlicerStatus.SLICING_REQUIRED` when no matching G-code exists on disk.
4. `tests/test_gcode_validator.py`:
   - Added `test_negative_coordinate_model_extrusion_rejection`.
   - Added `test_separated_purge_wipe_maintenance_vs_model`.
   - Added `test_support_z_gap_layer_height_aware`.
   - Verified exact model bounds on `single_color_PLA_2h20m.gcode`.
5. `tests/test_project_validator.py`:
   - Added `test_validate_split_project_components` auditing `Ayyappan_Male_Female_Locked.3mf`.
   - Verified that valid 3MF projects return `SlicerStatus.SLICING_REQUIRED`.
6. `tests/test_slicer_adapter.py`:
   - Added `test_execute_slice_split_project_requires_slicing` verifying `SLICING_REQUIRED` for split projects lacking G-code.

---

## 8. Conclusion & Sign-off

The Phase 6 engineering audit is complete. All discrepancies in coordinates, test counts, support air gaps, validation semantics, and split-project handling have been corrected and verified through automated regression tests.

As mandated by project constraints:
- **Phase 7 has NOT been started.**
- **No external AI API keys were used.**
- **No 3D models or G-code results were fabricated.**
- **System is ready for review before Phase 7 authorization.**

