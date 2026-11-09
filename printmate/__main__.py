"""
PRINTMATE AI – Unified Command Line Interface.
Provides single-command invocation for inspection, optimization, splitting,
connector generation, and native Bambu Studio project generation.

Usage:
    python -m printmate run <model_path> [options]
    python -m printmate inspect <model_path>
    python -m printmate optimize <model_path> [options]
    python -m printmate split <model_path> [options]
    python -m printmate validate <project_3mf>
"""

import sys
import os
import argparse
from typing import Optional

from printmate.core.config import Config
from printmate.workflow.orchestrator import WorkflowOrchestrator
from printmate.optimization.mesh_optimizer import MeshOptimizer, QualityLevel
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.slicer.project_validator import NativeProjectValidator
from printmate.splitting.multi_splitter import MultiSplitter
from printmate.geometry.loader import load_mesh

def cmd_run(args):
    """Executes the full end-to-end production workflow."""
    orchestrator = WorkflowOrchestrator(verbose=True)
    res = orchestrator.run_end_to_end(
        model_path=args.model_path,
        output_3mf=args.output,
        mode=args.mode,
        connector_type=args.connector,
        quality=args.quality,
        decimate=args.decimate,
        filament=args.filament,
        objective=args.objective,
        printer=args.printer,
        auto_confirm=args.yes,
        launch=args.open
    )
    if res.get("success"):
        sys.exit(0)
    else:
        sys.exit(1)

def cmd_inspect(args):
    """Inspects 3D geometry and checks printability constraints."""
    info = GeometryAnalyzer.analyze(args.model_path)
    mesh = load_mesh(args.model_path)
    exceeds, reasons = MultiSplitter.check_exceeds_volume(mesh)

    print(f"\n{'='*60}")
    print(f"PRINTMATE AI – Model Inspection: {os.path.basename(args.model_path)}")
    print(f"{'='*60}")
    print(f"Dimensions: {info.dim_x:.2f}mm (X) x {info.dim_y:.2f}mm (Y) x {info.dim_z:.2f}mm (Height)")
    print(f"Triangles:  {info.faces:,}")
    print(f"Watertight: {'Yes (Perfect)' if info.is_watertight else 'No (Open Boundaries)'}")
    print(f"Volume:     {info.volume_cm3:.2f} cm³")
    print(f"Fits A1 Bed:{'Yes' if not exceeds else 'NO (Exceeds volume)'}")
    if exceeds:
        for r in reasons:
            print(f"  - [!] {r}")
    print(f"{'='*60}\n")

def cmd_optimize(args):
    """Runs adaptive polygon decimation on high-poly meshes."""
    q = QualityLevel(args.quality) if args.quality in QualityLevel.__members__.values() else QualityLevel.BALANCED
    out = args.output or os.path.splitext(args.model_path)[0] + "_optimized.stl"
    metrics = MeshOptimizer.optimize(
        input_path=args.model_path,
        output_path=out,
        quality=q
    )
    print(f"\n{metrics.summary()}\n")
    if metrics.is_accepted:
        print(f"[OK] Optimized mesh saved to: {out}")
    else:
        print(f"[REJECTED] Optimization failed quality gates: {metrics.rejection_reason}")

def cmd_validate(args):
    """Audits a generated Bambu Studio .3mf archive."""
    report = NativeProjectValidator.validate_project(args.project_path)
    print(f"\n{report.summary()}\n")

def cmd_calibrate(args):
    """Generates physical test coupon gauge and fit calibration worksheet."""
    from printmate.connectors.calibration_generator import CalibrationGenerator
    from printmate.connectors.connector_generator import ConnectorType
    out_dir = args.output or os.path.join(Config.WORKSPACE_DIR, "outputs", "calibration")
    ctype = ConnectorType(args.connector) if args.connector in ConnectorType.__members__.values() else ConnectorType.D_SHAPED
    clearances = [float(x) for x in args.clearances] if args.clearances else [0.15, 0.20, 0.25, 0.30]
    res = CalibrationGenerator.generate_calibration_coupons(
        output_dir=out_dir,
        connector_type=ctype,
        clearances=clearances,
        material=args.filament
    )
    print(f"\n{'='*60}")
    print(f"PRINTMATE AI – Physical Calibration Gauge Generated")
    print(f"{'='*60}")
    print(f"Male Coupon:     {res.male_coupon_path}")
    print(f"Female Sockets:  {res.female_coupon_path}")
    print(f"Bambu 3MF Project: {res.project_3mf_path}")
    print(f"Worksheet:       {res.worksheet_md_path}")
    print(f"Clearances:      {res.clearances_tested} mm")
    print(f"{'='*60}\n")

def cmd_assemble(args):
    """Simulates virtual assembly of split parts and validates bounding box."""
    from printmate.assembly.assembly_simulator import AssemblySimulator
    rep = AssemblySimulator.simulate_assembly(
        parts=args.parts,
        original_mesh=args.original
    )
    print(f"\n{rep.summary()}\n")

def cmd_settings(args):
    """Inspects and optimizes print settings for a given model, material, printer, and objective."""
    from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
    from printmate.optimization.settings_validator import SettingsValidator
    from printmate.geometry.loader import load_mesh
    import json

    mesh = load_mesh(args.model_path) if os.path.exists(args.model_path) else None
    obj = OptimizationObjective(args.objective) if args.objective in [o.value for o in OptimizationObjective] else OptimizationObjective.BALANCED_QUALITY

    settings = SettingsEngine.optimize(
        mesh_or_info=mesh,
        filament_id=args.filament,
        printer_id=args.printer,
        objective=obj,
        has_connectors=args.has_connectors
    )

    if args.json:
        print(json.dumps(settings.to_slicer_overrides(), indent=2))
        return

    print(f"\n{'='*70}")
    print(f"PRINTMATE AI – Intelligent Print Settings Optimization")
    print(f"Target Printer: {settings.printer.name}")
    print(f"Filament:       {settings.filament.brand} {settings.filament.material_name} ({settings.filament.category.value.upper()})")
    print(f"Objective:      {settings.objective.value.upper()}")
    print(f"{'='*70}")
    print(f"Layer Height:         {settings.layer_height:.2f} mm (Initial: {settings.initial_layer_height:.2f} mm)")
    has_conn_reinf = "connectors" in settings.reasoning
    print(f"Wall Loops:           {settings.wall_loops} (Connector reinforcement: {'Yes (Hoop Strength >= 4)' if has_conn_reinf else 'No'})")
    print(f"Wall Generator:       {settings.wall_generator}")
    print(f"Top / Bottom Shells:  {settings.top_shell_layers} top / {settings.bottom_shell_layers} bottom")
    print(f"Infill:               {settings.sparse_infill_density} {settings.sparse_infill_pattern}")
    print(f"Print Speeds:         Outer {settings.outer_wall_speed_mm_s} mm/s | Inner {settings.inner_wall_speed_mm_s} mm/s | Infill {settings.sparse_infill_speed_mm_s} mm/s")
    print(f"Max Volumetric Speed: {settings.filament.max_volumetric_speed_mm3_s:.1f} mm3/s")
    print(f"Thermals:             Nozzle {settings.nozzle_temperature:.0f}C | Bed {settings.bed_temperature:.0f}C")
    print(f"Cooling Fans:         Part Cooling {settings.filament.cooling_fan_min_pct:.0f}-{settings.filament.cooling_fan_max_pct:.0f}%")
    print(f"Retraction:           {settings.filament.retraction_length_mm:.1f} mm at {settings.filament.retraction_speed_mm_s:.0f} mm/s")
    print(f"Supports:             Enabled: {settings.enable_support} (Type: {settings.support_type}, Style: {settings.support_style}, Angle: {settings.support_threshold_angle}deg)")
    print(f"Brim / Adhesion:      Brim Type: {settings.brim_type} (Width: {settings.brim_width_mm:.1f} mm)")
    print(f"{'-'*70}")
    print(f"ESTIMATES (Mathematical heuristic predictions - verify in slicer):")
    print(f"Estimated Duration:   ~{settings.estimated_print_time_mins:.0f} minutes ({settings.estimated_print_time_mins / 60.0:.1f} hours)")
    print(f"Estimated Material:   ~{settings.estimated_filament_grams:.1f} g")
    print(f"{'-'*70}")
    print(f"COMPATIBILITY AUDIT:")
    compat = SettingsValidator.validate_settings(settings, args.printer, args.filament)
    if compat.is_compatible:
        print(f"  [OK] Profile fully compatible with {settings.printer.name}.")
    else:
        print(f"  [CRITICAL ERROR] Incompatible configuration:")
        for err in compat.errors:
            print(f"    - [X] {err}")
    if compat.warnings:
        print(f"  Warnings & Precautions:")
        for w in compat.warnings:
            print(f"    - [!] {w}")
    if compat.operational_notes:
        print(f"  Operational Notes:")
        for note in compat.operational_notes:
            print(f"    - [*] {note}")
    print(f"{'-'*70}")
    print(f"ENGINEERING RATIONALE:")
    for k, v in settings.reasoning.items():
        print(f"  - {k}: {v}")
    print(f"{'='*70}\n")

def cmd_slice(args):
    """Executes slicer capability check, validates 3MF project, and initiates slicing."""
    from printmate.slicer.slicer_adapter import SlicerAdapter
    from printmate.slicer.gcode_validator import GCodeValidator
    from printmate.slicer.project_validator import NativeProjectValidator

    print(f"\n{'='*70}")
    print(f"PRINTMATE AI – Slicer Integration & Validation Engine")
    print(f"{'='*70}")

    # 1. Project audit
    proj_rep = NativeProjectValidator.validate_project(args.project_path)
    print(proj_rep.summary())
    if not proj_rep.is_valid:
        print("[ABORT] 3MF project failed validation. Fix project before slicing.")
        sys.exit(1)

    # 2. Slicer execution / GUI launch
    rec = SlicerAdapter.execute_slice(
        project_3mf=args.project_path,
        printer_profile=args.printer,
        filament_profile=args.filament,
        output_gcode=args.gcode,
        auto_launch_gui=not args.no_gui
    )
    print(f"\n{rec.summary()}")

    # 3. G-code audit if found
    if rec.gcode_path and os.path.exists(rec.gcode_path):
        print(f"\n{'='*70}")
        print(f"G-CODE TELEMETRY & PHYSICAL INTEGRITY AUDIT")
        print(f"{'='*70}")
        gcode_res = GCodeValidator.validate_gcode(rec.gcode_path, expected_printer=args.printer)
        print(gcode_res.summary())

    print(f"Physical Print Status: PHYSICAL_PRINT_NOT_VERIFIED")
    print(f"{'='*70}\n")

def cmd_validate_gcode(args):
    """Validates real Bambu Studio G-code file, extracts actual telemetry and audits build volume."""
    from printmate.slicer.gcode_validator import GCodeValidator
    res = GCodeValidator.validate_gcode(args.gcode_path, expected_printer=args.printer)
    print(f"\n{res.summary()}\n")
    if not res.is_valid:
        sys.exit(1)

def cmd_compare(args):
    """Performs side-by-side optimization comparison between heuristic predictions and actual slicer data."""
    from printmate.optimization.comparison_engine import OptimizationComparisonEngine
    from printmate.slicer.gcode_validator import GCodeValidator
    from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
    from printmate.geometry.loader import load_mesh

    mesh = load_mesh(args.model_path) if os.path.exists(args.model_path) else None
    obj = OptimizationObjective(args.objective) if args.objective in [o.value for o in OptimizationObjective] else OptimizationObjective.BALANCED_QUALITY
    settings = SettingsEngine.optimize(mesh, objective=obj, filament_id=args.filament, printer_id=args.printer)
    gcode_res = GCodeValidator.validate_gcode(args.gcode_path, expected_printer=args.printer)

    if not gcode_res.metadata:
        print(f"[ERROR] Failed to extract G-code metadata from {args.gcode_path}")
        sys.exit(1)

    rep = OptimizationComparisonEngine.compare_heuristic_vs_actual_slicer(
        heuristic_settings=settings,
        actual_gcode=gcode_res.metadata,
        model_name=os.path.basename(args.model_path)
    )
    print(f"\n{rep.summary()}\n")

def main():
    parser = argparse.ArgumentParser(
        prog="printmate",
        description="PRINTMATE AI – Autonomous 3D Print Preparation Engine for Bambu Lab A1"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. RUN
    p_run = subparsers.add_parser("run", help="Execute complete end-to-end print preparation")
    p_run.add_argument("model_path", help="Path to input 3D model (.stl, .obj, .3mf)")
    p_run.add_argument("-o", "--output", default=None, help="Output .3mf project path")
    p_run.add_argument("-m", "--mode", default="auto", choices=["auto", "single", "split"], help="Print strategy mode")
    p_run.add_argument("-c", "--connector", default="d_shaped", choices=["d_shaped", "keyed", "dual_pin", "asymmetric", "cylindrical", "none"], help="Connector type")
    p_run.add_argument("-q", "--quality", default="balanced", choices=["preserve_detail", "balanced", "aggressive"], help="Decimation quality level")
    p_run.add_argument("-d", "--decimate", default="auto", choices=["auto", "always", "never"], help="Decimation trigger")
    p_run.add_argument("-f", "--filament", default="pla_basic", help="Filament profile key (e.g. pla_basic, pla_matte, petg, abs, tpu, pla_cf)")
    p_run.add_argument("-b", "--objective", default="balanced_quality", choices=[
        "fine_detail", "balanced_quality", "strong_functional", "fast_printing", "minimum_material", "support_minimized"
    ], help="Optimization objective preset")
    p_run.add_argument("-p", "--printer", default="Bambu Lab A1", choices=[
        "Bambu Lab A1", "Bambu Lab X1-Carbon", "Prusa MK4", "Creality K1", "Creality Ender 3 V3", "Anycubic Kobra 2"
    ], help="Target 3D printer hardware profile")
    p_run.add_argument("-y", "--yes", action="store_true", help="Auto-confirm all prompts without pausing")
    p_run.add_argument("--open", "--launch", dest="open", action="store_true", help="Launch Bambu Studio with generated project")
    p_run.set_defaults(func=cmd_run)

    # 2. INSPECT
    p_insp = subparsers.add_parser("inspect", help="Deep inspection of model geometry and printability")
    p_insp.add_argument("model_path", help="Path to 3D model")
    p_insp.set_defaults(func=cmd_inspect)

    # 3. OPTIMIZE
    p_opt = subparsers.add_parser("optimize", help="Adaptive polygon optimization / decimation")
    p_opt.add_argument("model_path", help="Path to input model")
    p_opt.add_argument("-o", "--output", default=None, help="Output optimized STL path")
    p_opt.add_argument("-q", "--quality", default="balanced", choices=["preserve_detail", "balanced", "aggressive"], help="Quality preset")
    p_opt.set_defaults(func=cmd_optimize)

    # 4. VALIDATE
    p_val = subparsers.add_parser("validate", help="Audit Bambu Studio .3mf project against machine profile")
    p_val.add_argument("project_path", help="Path to .3mf project file")
    p_val.set_defaults(func=cmd_validate)

    # 5. CALIBRATE
    p_cal = subparsers.add_parser("calibrate", help="Generate physical connector clearance calibration coupons")
    p_cal.add_argument("-c", "--connector", default="d_shaped", choices=["d_shaped", "keyed", "dual_pin", "asymmetric", "cylindrical"], help="Connector type")
    p_cal.add_argument("--clearances", nargs="+", default=["0.15", "0.20", "0.25", "0.30"], help="Clearance steps in mm")
    p_cal.add_argument("-f", "--filament", default="pla_basic", help="Filament profile key")
    p_cal.add_argument("-o", "--output", default=None, help="Output directory")
    p_cal.set_defaults(func=cmd_calibrate)

    # 6. ASSEMBLE
    p_asm = subparsers.add_parser("assemble", help="Simulate assembly reconstruction from split parts")
    p_asm.add_argument("parts", nargs="+", help="Paths to split part STLs")
    p_asm.add_argument("--original", default=None, help="Path to original uncut reference model")
    p_asm.set_defaults(func=cmd_assemble)

    # 7. SETTINGS
    p_set = subparsers.add_parser("settings", help="Inspect and recommend optimized print settings")
    p_set.add_argument("model_path", help="Path to 3D model file")
    p_set.add_argument("-f", "--filament", default="pla_basic", help="Filament material key")
    p_set.add_argument("-p", "--printer", default="Bambu Lab A1", choices=[
        "Bambu Lab A1", "Bambu Lab X1-Carbon", "Prusa MK4", "Creality K1", "Creality Ender 3 V3", "Anycubic Kobra 2"
    ], help="Target 3D printer profile")
    p_set.add_argument("-b", "--objective", default="balanced_quality", choices=[
        "fine_detail", "balanced_quality", "strong_functional", "fast_printing", "minimum_material", "support_minimized"
    ], help="Print optimization objective")
    p_set.add_argument("--has-connectors", action="store_true", help="Reinforce perimeter wall loops for split pins/sockets")
    p_set.add_argument("--supports-required", action="store_true", help="Enable and configure support structures")
    p_set.add_argument("--json", action="store_true", help="Output raw slicer overrides JSON")
    p_set.set_defaults(func=cmd_settings)

    # 8. SLICE
    p_slc = subparsers.add_parser("slice", help="Validate and slice 3MF project with Bambu Studio")
    p_slc.add_argument("project_path", help="Path to .3mf project file")
    p_slc.add_argument("-p", "--printer", default="Bambu Lab A1", help="Target 3D printer profile")
    p_slc.add_argument("-f", "--filament", default="pla_basic", help="Filament profile key")
    p_slc.add_argument("-g", "--gcode", default=None, help="Explicit target or existing G-code path")
    p_slc.add_argument("--no-gui", action="store_true", help="Do not launch interactive Bambu Studio GUI window")
    p_slc.set_defaults(func=cmd_slice)

    # 9. VALIDATE-GCODE
    p_vgc = subparsers.add_parser("validate-gcode", help="Audit real Bambu Studio G-code file and telemetry")
    p_vgc.add_argument("gcode_path", help="Path to .gcode file")
    p_vgc.add_argument("-p", "--printer", default="Bambu Lab A1", help="Expected printer profile")
    p_vgc.set_defaults(func=cmd_validate_gcode)

    # 10. COMPARE
    p_cmp = subparsers.add_parser("compare", help="Compare heuristic predictions with actual Bambu Studio G-code")
    p_cmp.add_argument("model_path", help="Path to input 3D model")
    p_cmp.add_argument("-g", "--gcode-path", required=True, help="Path to sliced .gcode file")
    p_cmp.add_argument("-b", "--objective", default="fine_detail", choices=[
        "fine_detail", "balanced_quality", "strong_functional", "fast_printing", "minimum_material", "support_minimized"
    ], help="Optimization objective preset")
    p_cmp.add_argument("-f", "--filament", default="pla_basic", help="Filament profile key")
    p_cmp.add_argument("-p", "--printer", default="Bambu Lab A1", help="Target printer profile")
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
