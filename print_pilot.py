"""
=============================================================================
Antigravity Bambu Lab PrintPilot Automation Engine (Backward-Compatible CLI)
Target Machine: Bambu Lab A1 (0.4mm Nozzle)
=============================================================================
This file serves as the backward-compatible entry point for PrintMate AI,
delegating all operations to the modular 'printmate' package architecture.
"""

import os
import sys
import argparse
from typing import Dict, Any, Optional

from printmate.core.config import Config
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.slicer.project_generator import BambuProjectGenerator
from printmate.slicer.bambu_bridge import BambuBridge
from printmate.workflow.orchestrator import WorkflowOrchestrator

WORKSPACE_DIR = Config.WORKSPACE_DIR
BAMBU_STUDIO_EXE = Config.BAMBU_STUDIO_EXE
GOLDEN_TEMPLATE_3MF = Config.GOLDEN_TEMPLATE_3MF

def analyze_model(model_path: str) -> Dict[str, Any]:
    """
    Deep inspection of 3D geometry (Backward-compatible wrapper).
    """
    print(f"\n[*] Scanning model: {os.path.basename(model_path)}")
    info = GeometryAnalyzer.analyze(model_path)
    
    print(f"    - Dimensions: {info.dim_x:.2f} mm (X) x {info.dim_y:.2f} mm (Y) x {info.dim_z:.2f} mm (Height)")
    print(f"    - Polygons: {info.faces:,} triangles")
    print(f"    - Watertight: {'Yes (Perfect)' if info.is_watertight else 'Needs auto-seal (Trivial)'}")
    if info.dim_z < 65:
        print("    - [!] Miniature Scale detected (<65mm). Requiring 0.24mm safe-Z air gap to prevent hand breakages.")
        
    return {
        "file": info.file,
        "filename": info.filename,
        "vertices": info.vertices,
        "faces": info.faces,
        "dim_x": info.dim_x,
        "dim_y": info.dim_y,
        "dim_z": info.dim_z,
        "is_watertight": info.is_watertight,
        "volume_cm3": info.volume_cm3
    }

def create_safe_bambu_project(
    input_file: str,
    output_3mf: str,
    mode: str = "single",
    filament: str = "pla_basic",
    target_height: Optional[float] = None
) -> str:
    """
    Builds a native Bambu Studio .3mf project file (Backward-compatible wrapper).
    """
    print(f"\n[*] Generating Bambu Studio Project: {os.path.basename(output_3mf)}")
    if target_height is not None:
        scale_pct = (float(target_height) / 100.0) * 100.0
        print(f"    - Scaling model uniformly to {scale_pct:.1f}% (Height = {target_height} mm)")

    out_path = BambuProjectGenerator.generate(
        input_file=input_file,
        output_3mf=output_3mf,
        mode=mode,
        filament=filament,
        target_height=target_height
    )
    print(f"[OK] Project generated successfully at: {out_path}")
    return out_path

def launch_bambu_studio(project_3mf: str) -> None:
    """
    Launches Bambu Studio directly with the ready project (Backward-compatible wrapper).
    """
    print("\n[*] Launching Bambu Studio with project...")
    BambuBridge.launch(project_3mf)
    print("[OK] Bambu Studio is now opening on your screen!")

def main():
    default_model = os.path.join(WORKSPACE_DIR, "models", "raw", "single_color.stl")
    if not os.path.exists(default_model):
        default_model = os.path.join(WORKSPACE_DIR, "single_color.stl")

    parser = argparse.ArgumentParser(description="Antigravity Bambu PrintPilot Automation")
    parser.add_argument("--model", default=default_model, help="Path to input STL")
    parser.add_argument("--mode", default="single", choices=["single", "split"], help="Single piece with safe supports or Split support-free")
    parser.add_argument("--filament", default="pla_basic", choices=["pla_basic", "pla_silk", "pla_matte", "petg"], help="Filament type")
    parser.add_argument("--height", type=float, default=55.0, help="Target height in mm (e.g. 55, 75, 100)")
    parser.add_argument("--launch", action="store_true", help="Launch Bambu Studio after build")
    args = parser.parse_args()

    orchestrator = WorkflowOrchestrator(verbose=True)
    out_name = f"Ready_{os.path.splitext(os.path.basename(args.model))[0]}_{args.mode}_{int(args.height)}mm.3mf"
    out_path = os.path.join(WORKSPACE_DIR, out_name)

    result = orchestrator.run_pipeline(
        model_path=args.model,
        output_3mf=out_path,
        mode=args.mode,
        filament=args.filament,
        target_height=args.height,
        launch=args.launch
    )
    
    if not result.success:
        sys.exit(1)

if __name__ == "__main__":
    main()
