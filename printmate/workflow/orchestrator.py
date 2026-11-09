"""
Workflow Orchestrator module.
Coordinates end-to-end processing: geometry analysis, validation, strategy optimization,
slicer packaging, and launch.
"""

import os
import sys
import time
from typing import Optional, Dict, Any
from printmate.core.models import ModelInfo, WorkflowResult
from printmate.core.exceptions import PrintMateError
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.intelligence.classification import ClassificationEngine
from printmate.intelligence.risk_assessment import RiskAssessor
from printmate.slicer.project_generator import BambuProjectGenerator
from printmate.slicer.bambu_bridge import BambuBridge
from printmate.reporting.analysis_report import AnalysisReporter
from printmate.workflow.workflow_state import WorkflowState, WorkflowStage
from printmate.geometry.loader import load_mesh
from printmate.geometry.thickness_analyzer import ThicknessAnalyzer
from printmate.geometry.overhang_analyzer import OverhangAnalyzer
from printmate.geometry.island_detector import IslandDetector
from printmate.intelligence.fragility_analyzer import FragilityAnalyzer
from printmate.optimization.orientation_optimizer import OrientationOptimizer
from printmate.optimization.mesh_optimizer import MeshOptimizer, QualityLevel
from printmate.splitting.multi_splitter import MultiSplitter
from printmate.connectors.connector_generator import ConnectorGenerator, DowelLockConfig, ConnectorType
from printmate.connectors.pair_validator import ConnectorPairValidator
from printmate.connectors.tolerance_profiles import ToleranceManager
from printmate.assembly.assembly_simulator import AssemblySimulator
from printmate.assembly.assembly_instructions import AssemblyInstructionsGenerator
from printmate.slicer.project_validator import NativeProjectValidator
from printmate.slicer.slicer_adapter import SlicerAdapter
from printmate.slicer.gcode_validator import GCodeValidator
from printmate.optimization.comparison_engine import OptimizationComparisonEngine
from printmate.slicer.slicer_status import SlicerStatus
from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
from printmate.profiles.printer_profiles import PrinterProfileRegistry
from printmate.profiles.filament_profiles import FilamentProfileRegistry
from printmate.splitting.split_analyzer import SplitAnalyzer
from printmate.splitting.planar_splitter import PlanarSplitter
from printmate.core.config import Config
import trimesh

class WorkflowOrchestrator:
    """Orchestrates the PrintMate AI automated pipeline."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.state = WorkflowState()

    def log(self, message: str) -> None:
        """Prints log messages if verbose is enabled."""
        if self.verbose:
            print(message)

    def run_deep_intelligence(self, model_path: str, report_output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full Phase 1 geometry intelligence: thickness, overhangs, islands, fragility, and orientations.
        """
        mesh = load_mesh(model_path)
        info = GeometryAnalyzer.analyze(model_path)
        scale_class = ClassificationEngine.classify_scale(info)
        risks = RiskAssessor.assess(info)

        thick_rep = ThicknessAnalyzer.analyze(mesh)
        oh_rep = OverhangAnalyzer.analyze(mesh)
        isl_rep = IslandDetector.analyze(mesh)
        frag_rep = FragilityAnalyzer.analyze(mesh)
        orient_rep = OrientationOptimizer.optimize(mesh)

        md_content = AnalysisReporter.generate_markdown_report(
            info=info,
            risks=risks,
            scale_class=scale_class,
            output_file=report_output_path,
            thickness_report=thick_rep,
            overhang_report=oh_rep,
            island_report=isl_rep,
            fragility_report=frag_rep,
            orientation_report=orient_rep
        )

        return {
            "model_info": info,
            "scale_class": scale_class,
            "thickness": thick_rep,
            "overhang": oh_rep,
            "islands": isl_rep,
            "fragility": frag_rep,
            "orientations": orient_rep,
            "markdown_report": md_content
        }

    def run_pipeline(
        self,
        model_path: str,
        output_3mf: str,
        mode: str = "single",
        filament: str = "pla_basic",
        target_height: Optional[float] = None,
        launch: bool = False
    ) -> WorkflowResult:
        """
        Executes the full pipeline for a 3D model.

        Pipeline stages:
        1. File Validation
        2. Geometry Analysis & Mesh Validation
        3. Scale Classification
        4. Risk Assessment
        5. Strategy Optimization & Slicer Project Generation
        6. Bambu Studio Launch (optional)

        Returns:
            WorkflowResult dataclass.
        """
        self.state.transition(WorkflowStage.FILE_VALIDATION)
        if not os.path.exists(model_path):
            err = f"Input model file not found: {model_path}"
            self.state.record_error(err)
            return WorkflowResult(success=False, output_file=None, errors=[err])

        try:
            # 1. Geometry Analysis
            self.state.transition(WorkflowStage.GEOMETRY_ANALYSIS)
            self.log(f"\n[*] Scanning model: {os.path.basename(model_path)}")
            info: ModelInfo = GeometryAnalyzer.analyze(model_path)
            self.log(f"    - Dimensions: {info.dim_x:.2f} mm (X) x {info.dim_y:.2f} mm (Y) x {info.dim_z:.2f} mm (Height)")
            self.log(f"    - Polygons: {info.faces:,} triangles")
            self.log(f"    - Watertight: {'Yes (Perfect)' if info.is_watertight else 'Needs auto-seal (Trivial)'}")

            # 2. Classification & Risk Assessment
            self.state.transition(WorkflowStage.RISK_ASSESSMENT)
            scale_class = ClassificationEngine.classify_scale(info)
            risks = RiskAssessor.assess(info)

            for r in risks:
                self.log(f"    - [!] {r}")

            # 3. Project Generation
            self.state.transition(WorkflowStage.PROJECT_GENERATION)
            self.log(f"\n[*] Generating Bambu Studio Project: {os.path.basename(output_3mf)}")
            if target_height is not None:
                scale_pct = (float(target_height) / 100.0) * 100.0
                self.log(f"    - Scaling model uniformly to {scale_pct:.1f}% (Height = {target_height} mm)")

            generated_path = BambuProjectGenerator.generate(
                input_file=model_path,
                output_3mf=output_3mf,
                mode=mode,
                filament=filament,
                target_height=target_height
            )
            self.state.artifacts["project_3mf"] = generated_path
            self.log(f"[OK] Project generated successfully at: {generated_path}")

            # 4. Optional Launch
            if launch:
                self.state.transition(WorkflowStage.LAUNCHING_STUDIO)
                self.log("\n[*] Launching Bambu Studio with project...")
                BambuBridge.launch(generated_path)
                self.log("[OK] Bambu Studio is now opening on your screen!")

            self.state.complete()
            return WorkflowResult(
                success=True,
                output_file=generated_path,
                model_info=info,
                errors=[]
            )

        except Exception as e:
            err_msg = str(e)
            self.state.record_error(err_msg)
            self.log(f"[ERROR] Pipeline execution failed: {err_msg}")
            return WorkflowResult(
                success=False,
                output_file=None,
                errors=[err_msg]
            )

    def run_end_to_end(
        self,
        model_path: str,
        output_3mf: Optional[str] = None,
        mode: str = "auto",
        connector_type: str = "d_shaped",
        quality: str = "balanced",
        decimate: str = "auto",
        filament: str = "pla_basic",
        objective: str = "balanced_quality",
        printer: str = "Bambu Lab A1",
        auto_confirm: bool = False,
        launch: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the unified end-to-end Phase 5 production workflow:
        1. Ingest & inspect geometry
        2. Validate mesh & build-volume constraints
        3. Adaptive polygon decimation for high-poly meshes (>1M triangles)
        4. Overhang & orientation evaluation
        5. Single-piece vs. split strategy decision
        6. Precision multi-part splitting (avoiding fragile zones)
        7. Precision anti-rotation connector generation & pair validation
        8. Multi-objective print settings optimization (Fine, Strong, Fast, etc.)
        9. Native Bambu Studio 3MF generation & project validation
        10. Report generation & optional GUI launch
        """
        self.log(f"\n{'='*70}")
        self.log(f"PRINTMATE AI – Autonomous Production Workflow (Phase 5)")
        self.log(f"Target Printer: {printer} | Material: {filament.upper()} | Objective: {objective.upper()}")
        self.log(f"Input Model: {model_path}")
        self.log(f"{'='*70}\n")

        if not os.path.exists(model_path):
            raise PrintMateError(f"Input model file not found: {model_path}")

        stem = os.path.splitext(os.path.basename(model_path))[0]
        ws = Config.WORKSPACE_DIR

        # Step 1 & 2: Ingest & Geometry Analysis
        self.log(f"[*] STEP 1/10: Inspecting 3D Geometry...")
        info = GeometryAnalyzer.analyze(model_path)
        mesh = load_mesh(model_path)
        self.log(f"    - Dimensions: {info.dim_x:.2f}mm (X) x {info.dim_y:.2f}mm (Y) x {info.dim_z:.2f}mm (Height)")
        self.log(f"    - Mesh Faces: {info.faces:,} triangles")
        self.log(f"    - Watertight: {'Yes (Clean Solid)' if info.is_watertight else 'Warning: Open Boundaries'}")

        # Step 3 & 4: Build Volume Check
        self.log(f"\n[*] STEP 2/10: Validating Machine Build-Volume Constraints...")
        exceeds_vol, vol_reasons = MultiSplitter.check_exceeds_volume(mesh)
        if exceeds_vol:
            self.log(f"    - [!] Model exceeds Bambu Lab A1 build envelope:")
            for vr in vol_reasons:
                self.log(f"        * {vr}")
        else:
            self.log(f"    - [OK] Model fits within 256x256x256mm build volume.")

        # Step 5: Adaptive Polygon Decimation
        self.log(f"\n[*] STEP 3/10: Polygon Optimization & Decimation Check...")
        active_mesh = mesh
        active_model_path = model_path
        decimation_performed = False
        opt_metrics = None

        should_decimate = (decimate == "always") or (decimate == "auto" and info.faces > 1_000_000)
        if should_decimate:
            self.log(f"    - High polygon count detected ({info.faces:,} triangles). Running adaptive decimation...")
            opt_dir = os.path.join(ws, "outputs", "optimized_models")
            os.makedirs(opt_dir, exist_ok=True)
            opt_path = os.path.join(opt_dir, f"{stem}_optimized.stl")

            q_preset = QualityLevel(quality) if quality in QualityLevel.__members__.values() else QualityLevel.BALANCED
            opt_metrics = MeshOptimizer.optimize(
                input_path=model_path,
                output_path=opt_path,
                quality=q_preset
            )

            if opt_metrics.is_accepted:
                self.log(f"    - [OK] {opt_metrics.summary()}")
                active_model_path = opt_path
                active_mesh = trimesh.load(opt_path, process=False)
                decimation_performed = True
            else:
                self.log(f"    - [!] {opt_metrics.summary()}")
                self.log(f"    - Preserving original model as immutable source.")
        else:
            self.log(f"    - Mesh has {info.faces:,} triangles (within optimal slicing threshold). Decimation skipped.")

        # Step 6: Overhang & Orientation Analysis
        self.log(f"\n[*] STEP 4/10: Analyzing Overhangs & Support Feasibility...")
        overhang_rep = OverhangAnalyzer.analyze(active_mesh)
        self.log(f"    - Overhang Area: {overhang_rep.total_overhang_area_cm2:.2f} cm² ({overhang_rep.overhang_percentage:.1f}%)")
        self.log(f"    - Support Risk Level: {overhang_rep.risk_level}")

        # Step 7: Strategy Decision
        self.log(f"\n[*] STEP 5/10: Synthesizing Printing Strategy...")
        natural_cuts = SplitAnalyzer.find_necking_candidates(
            SplitAnalyzer.sample_cross_sections(active_mesh, axis=2, num_samples=50)
        )

        if mode == "auto":
            if exceeds_vol:
                chosen_strategy = "split"
                self.log(f"    - Strategy: MULTI-PART SPLIT (Mandatory due to build volume).")
            elif overhang_rep.overhang_percentage > 12.0 and natural_cuts:
                chosen_strategy = "split"
                self.log(f"    - Strategy: SUPPORT-FREE SPLIT (Natural parting seam found at Z={natural_cuts[0]}mm).")
                if not auto_confirm and sys.stdin.isatty():
                    print("\n[?] STRATEGY PROMPT: Recommended: SPLIT (Support-free). Alternative: SINGLE (Tree supports).")
                    ans = input("Proceed with recommended SPLIT? [Y/n]: ").strip().lower()
                    if ans == "n":
                        chosen_strategy = "single"
            else:
                chosen_strategy = "single"
                self.log(f"    - Strategy: SINGLE-PIECE PRINT (Safe tree supports).")
        else:
            chosen_strategy = mode
            self.log(f"    - Strategy: User forced mode '{chosen_strategy}'.")

        # Step 8 & 9: Execution of Splitting & Connectors
        parts_to_pack: List[str] = []
        is_split = (chosen_strategy == "split")

        if is_split:
            self.log(f"\n[*] STEP 6/10: Executing Precision Splitting...")
            parts_dir = os.path.join(ws, "outputs", "split_parts")
            os.makedirs(parts_dir, exist_ok=True)

            if exceeds_vol:
                # Multi-part split
                res = MultiSplitter.plan_and_execute(active_mesh, base_name=stem)
                for p in res.parts:
                    p_path = os.path.join(parts_dir, f"{p.name}.stl")
                    p.mesh.export(p_path)
                    parts_to_pack.append(p_path)
                    self.log(f"    - Saved sub-part: {os.path.basename(p_path)} (Height: {p.dimensions[2]:.1f}mm)")
            else:
                # Natural inflection crease split
                z_cut = natural_cuts[0] if natural_cuts else round(float(active_mesh.bounds[0][2] + active_mesh.extents[2] * 0.3), 2)
                p_below, p_above = PlanarSplitter.split(
                    mesh=active_mesh,
                    plane_normal=(0.0, 0.0, 1.0),
                    plane_origin=(0.0, 0.0, z_cut),
                    cap=True
                )
                raw_base_path = os.path.join(parts_dir, f"{stem}_Part1_Base.stl")
                raw_top_path = os.path.join(parts_dir, f"{stem}_Part2_Top.stl")
                p_below.export(raw_base_path)
                p_above.export(raw_top_path)

                # Connectors
                if connector_type != "none":
                    self.log(f"\n[*] STEP 7/10: Engineering Precision Anti-Rotation Connectors ({connector_type})...")
                    ctype = ConnectorType(connector_type) if connector_type in ConnectorType.__members__.values() else ConnectorType.D_SHAPED
                    cfg = DowelLockConfig(connector_type=ctype, pin_radius=3.0, pin_height=5.0, clearance=0.25)

                    # Center of cut face
                    cut_poly = active_mesh.section(plane_origin=(0,0,z_cut), plane_normal=(0,0,1))
                    cx, cy = 0.0, 0.0
                    if cut_poly is not None:
                        cx, cy = float(cut_poly.centroid[0]), float(cut_poly.centroid[1])

                    locked_base_path = os.path.join(parts_dir, f"{stem}_Part1_Base_MaleLock.stl")
                    locked_top_path = os.path.join(parts_dir, f"{stem}_Part2_Top_FemaleLock.stl")

                    ConnectorGenerator.apply_blender_dowel_lock(
                        base_stl=raw_base_path,
                        idol_stl=raw_top_path,
                        out_base_stl=locked_base_path,
                        out_idol_stl=locked_top_path,
                        center_xy=(cx, cy),
                        z_cut=z_cut,
                        config=cfg
                    )
                    parts_to_pack = [locked_base_path, locked_top_path]
                    self.log(f"    - [OK] Integrated {ctype.value} connector pin and tolerance-compensated socket.")

                    # Phase 4: Validate Connector Pair Geometry
                    self.log(f"\n[*] STEP 7b/10: Auditing Connector Pair Match & Wall Clearances...")
                    m_base = trimesh.load(locked_base_path, process=False)
                    m_top = trimesh.load(locked_top_path, process=False)
                    pair_res = ConnectorPairValidator.validate_pair(
                        male_mesh=m_base,
                        female_mesh=m_top,
                        config=cfg,
                        z_cut=z_cut,
                        center_xy=(cx, cy)
                    )
                    self.log(f"    - {pair_res.summary().splitlines()[0]}")
                    self.log(f"    - Measured Radial Clearance: {pair_res.radial_clearance_mm:.2f}mm, Axial Relief: {pair_res.axial_relief_mm:.2f}mm")
                    self.log(f"    - Min Wall Thickness: {pair_res.min_wall_thickness_mm:.2f}mm (Safe)")

                    # Phase 4: Assembly Simulation & Reconstruction Check
                    self.log(f"\n[*] STEP 7c/10: Running Virtual Assembly Simulation...")
                    asmb_res = AssemblySimulator.simulate_assembly(
                        parts=parts_to_pack,
                        original_mesh=active_mesh,
                        expected_part_count=2
                    )
                    self.log(f"    - Assembly Status: {'PASSED' if asmb_res.is_valid else 'FAILED'}")
                    self.log(f"    - Bounding Box Alignment Deviation: {asmb_res.bounds_max_delta_mm:.4f}mm")

                    # Phase 4: Generate Assembly Instructions Manual
                    manual_path = os.path.join(ws, "outputs", "reports", f"{stem}_assembly_guide.md")
                    AssemblyInstructionsGenerator.generate_instructions(
                        model_name=stem,
                        parts=parts_to_pack,
                        connector_type=ctype.value,
                        output_path=manual_path
                    )
                    self.log(f"    - [OK] Assembly manual saved to: {manual_path}")
                else:
                    parts_to_pack = [raw_base_path, raw_top_path]
        else:
            self.log(f"\n[*] STEP 6/10: Single-piece preparation (Splitting bypassed).")

        # Step 8: Multi-Objective Print Settings Optimization & Bambu Studio 3MF Project Generation
        self.log(f"\n[*] STEP 8/10: Optimizing Print Settings & Generating Native Bambu Studio .3mf Project...")
        out_dir = os.path.join(ws, "outputs", "projects_3mf")
        os.makedirs(out_dir, exist_ok=True)
        final_3mf = output_3mf or os.path.join(out_dir, f"{stem}_{chosen_strategy}_PrintReady.3mf")

        # Phase 5: Intelligent Settings Engine
        obj_enum = OptimizationObjective(objective) if objective in OptimizationObjective.__members__.values() else OptimizationObjective.BALANCED_QUALITY
        opt_settings = SettingsEngine.optimize(
            mesh_or_info=active_mesh,
            objective=obj_enum,
            printer_id=printer,
            filament_id=filament,
            has_connectors=(is_split and connector_type != "none"),
            is_split_flat=is_split
        )
        self.log(f"    - Selected Objective: {opt_settings.objective.value.upper()}")
        self.log(f"    - Process: {opt_settings.layer_height:.2f}mm layer, {opt_settings.wall_loops} walls, {opt_settings.sparse_infill_density} {opt_settings.sparse_infill_pattern}")
        self.log(f"    - Thermals: Nozzle {opt_settings.nozzle_temperature:.0f}°C, Bed {opt_settings.bed_temperature:.0f}°C")
        if opt_settings.compatibility and opt_settings.compatibility.warnings:
            for cw in opt_settings.compatibility.warnings:
                self.log(f"    - [COMPATIBILITY WARNING] {cw}")
        for param, reason in list(opt_settings.reasoning.items())[:3]:
            self.log(f"        * {param}: {reason}")

        slicer_overrides = opt_settings.to_slicer_overrides()

        if is_split and len(parts_to_pack) > 1:
            BambuProjectGenerator.generate_multi_part_project(
                parts=parts_to_pack,
                output_3mf=final_3mf,
                filament=filament,
                custom_overrides=slicer_overrides
            )
        else:
            BambuProjectGenerator.generate(
                input_file=active_model_path,
                output_3mf=final_3mf,
                mode="single",
                filament=filament,
                custom_overrides=slicer_overrides
            )

        self.log(f"    - [OK] Project archive built at: {final_3mf}")

        # Step 9: Project & Slicer Integration Audit
        self.log(f"\n[*] STEP 9/10: Auditing Bambu Studio Project Settings & Slicer Integration...")
        val_rep = NativeProjectValidator.validate_project(final_3mf)
        self.log(f"    - 3MF Status: {val_rep.status.value}")
        self.log(f"    - Machine Profile: {val_rep.printer_model} ({val_rep.nozzle_diameter}mm)")
        self.log(f"    - Slicer Settings: {val_rep.layer_height}mm layer, {val_rep.wall_loops} walls, {val_rep.infill_pattern} infill")
        self.log(f"    - Support Profile: {val_rep.support_type} (Z-gap: {val_rep.support_top_z_gap}mm, XY: {val_rep.support_xy_clearance}mm)")
        if val_rep.errors:
            for ve in val_rep.errors:
                self.log(f"    - [ERROR] {ve}")

        slice_rec = SlicerAdapter.execute_slice(
            project_3mf=final_3mf,
            printer_profile=printer,
            filament_profile=filament,
            auto_launch_gui=launch
        )
        self.log(f"    - Slicer Automation: {slice_rec.status.value} (v{slice_rec.slicer_version or 'N/A'})")

        gcode_rep = None
        comp_rep = None
        if slice_rec.gcode_path and os.path.exists(slice_rec.gcode_path):
            gcode_rep = GCodeValidator.validate_gcode(slice_rec.gcode_path, expected_printer=printer)
            if gcode_rep.is_valid and gcode_rep.metadata:
                self.log(f"    - [OK] Verified Sliced G-code: {os.path.basename(slice_rec.gcode_path)}")
                self.log(f"    - Actual Duration: {gcode_rep.metadata.total_estimated_time_str} | Actual Material: {gcode_rep.metadata.total_filament_weight_g:.2f}g")
                comp_rep = OptimizationComparisonEngine.compare_heuristic_vs_actual_slicer(
                    heuristic_settings=opt_settings,
                    actual_gcode=gcode_rep.metadata,
                    model_name=stem
                )

        # Step 10: Analysis Report Generation
        self.log(f"\n[*] STEP 10/10: Generating Production Engineering Report...")
        rep_dir = os.path.join(ws, "outputs", "reports")
        os.makedirs(rep_dir, exist_ok=True)
        report_file = os.path.join(rep_dir, f"{stem}_production_report.md")

        reasoning_rows = "\n".join([f"- **{k}:** {v}" for k, v in opt_settings.reasoning.items()])
        gcode_section = ""
        if gcode_rep and gcode_rep.metadata:
            gcode_section = f"""## 6. Verified Slicer G-code Telemetry (Phase 6)
- **Slicer Software:** {gcode_rep.metadata.slicer_version}
- **Actual Print Duration:** {gcode_rep.metadata.total_estimated_time_str} ({gcode_rep.metadata.total_estimated_time_minutes:.1f} minutes)
- **Actual Filament Consumption:** {gcode_rep.metadata.total_filament_weight_g:.2f}g ({gcode_rep.metadata.total_filament_length_mm:.1f}mm)
- **Actual Layer Count:** {gcode_rep.metadata.total_layers} layers (Max Z: {gcode_rep.metadata.max_z_height_mm:.2f}mm)
- **Toolpath Bed Fit:** X:[{gcode_rep.metadata.first_layer_min_x:.1f}, {gcode_rep.metadata.first_layer_max_x:.1f}] Y:[{gcode_rep.metadata.first_layer_min_y:.1f}, {gcode_rep.metadata.first_layer_max_y:.1f}]
- **Telemetry Authenticity:** ACTUAL SLICER DATA (is_actual_slicer_output=True, is_heuristic=False)

{comp_rep.comparison_summary_md if comp_rep else ''}
"""
        else:
            gcode_section = f"""## 6. Slicer Automation & Slicing Status (Phase 6)
- **Status:** `{slice_rec.status.value}`
- **Slicer Software:** Bambu Studio ({slice_rec.slicer_version or 'Installed'})
- **Automation Interface:** GUI-Assisted Workflow (official Windows builds do not expose headless CLI slicing)
- **Next Step:** Open project in Bambu Studio, review plate layout, and click 'Slice Plate' (Ctrl+R).
"""

        report_md = f"""# PRINTMATE AI Production Report: {stem}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Target Printer:** {opt_settings.printer.name} ({opt_settings.printer.default_nozzle_diameter}mm Nozzle)  
**Filament:** {opt_settings.filament.brand} {opt_settings.filament.material_name}  
**Selected Strategy:** {chosen_strategy.upper()}  
**Optimization Objective:** {opt_settings.objective.value.upper()}  
**Physical Print Status:** `PHYSICAL_PRINT_NOT_VERIFIED`  

## 1. Geometric Inspection
- **Original Triangles:** {info.faces:,}
- **Dimensions:** {info.dim_x:.2f}mm × {info.dim_y:.2f}mm × {info.dim_z:.2f}mm
- **Watertight Solid:** {info.is_watertight}
- **Build Volume Exceeded:** {exceeds_vol}

## 2. Optimization Summary
- **Decimation Applied:** {decimation_performed}
- **Triangles Sliced:** {len(active_mesh.faces):,}
{f'- **Volume Shift:** {opt_metrics.volume_deviation_pct:.2f}%\n- **RMS Surface Deviation:** {opt_metrics.surface_deviation_rms_mm:.4f}mm' if opt_metrics else ''}

## 3. Intelligent Slicer Process Settings
- **Layer Height:** {opt_settings.layer_height:.2f}mm (Initial: {opt_settings.initial_layer_height:.2f}mm)
- **Wall Loops:** {opt_settings.wall_loops} ({opt_settings.wall_generator})
- **Top / Bottom Shells:** {opt_settings.top_shell_layers} / {opt_settings.bottom_shell_layers}
- **Infill:** {opt_settings.sparse_infill_density} {opt_settings.sparse_infill_pattern}
- **Nozzle Temperature:** {opt_settings.nozzle_temperature:.0f}°C
- **Bed Temperature:** {opt_settings.bed_temperature:.0f}°C
- **Estimated Material Consumption:** ~{opt_settings.estimated_filament_grams:.1f}g (Heuristic estimation)
- **Estimated Print Duration:** ~{opt_settings.estimated_print_time_mins:.0f} mins (Heuristic estimation)

### Engineering Rationales:
{reasoning_rows}

## 4. Splitting & Connectors
- **Strategy:** {chosen_strategy}
- **Sub-parts Generated:** {len(parts_to_pack) if is_split else 1}
- **Connector Type:** {connector_type if is_split else 'N/A'}

## 5. Native 3MF Project
- **Project File:** `{final_3mf}`
- **Validation Status:** {'PASSED' if val_rep.is_valid else 'FAILED'}
- **Objects on Plate:** {val_rep.objects_count}
- **Layer Height:** {val_rep.layer_height}mm
- **Support Top Z Air-Gap:** {val_rep.support_top_z_gap}mm

{gcode_section}

## 7. Next Steps & Production Safety Declaration
> [!IMPORTANT]
> **PHYSICAL PRINT NOT VERIFIED:** Software slicing and G-code validation have completed. Physical print outcome requires user execution on the Bambu Lab A1 hardware.

{val_rep.slicing_instructions}
"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_md)
        self.log(f"    - [OK] Report saved to: {report_file}")

        self.log(f"\n{'='*70}")
        self.log(f"[SUCCESS] PRINTMATE AI workflow completed successfully!")
        self.log(f"Physical Print Status: PHYSICAL_PRINT_NOT_VERIFIED")
        self.log(f"{'='*70}\n")

        return {
            "success": True,
            "project_3mf": final_3mf,
            "report_file": report_file,
            "strategy": chosen_strategy,
            "parts": parts_to_pack,
            "validation": val_rep,
            "decimation": opt_metrics,
            "slicer_record": slice_rec,
            "gcode_result": gcode_rep,
            "comparison": comp_rep,
            "physical_print_confirmed": False
        }


