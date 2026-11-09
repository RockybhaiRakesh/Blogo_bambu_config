"""
Print Settings Optimization and Machine Profile Routes.
"""

import os
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from printmate.api.schemas import SettingsOptimizeRequest, PrintSettingsResponse
from printmate.api.job_manager import JobManager
from printmate.profiles.printer_profiles import PrinterProfileRegistry
from printmate.profiles.filament_profiles import FilamentProfileRegistry
from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
from printmate.optimization.settings_validator import SettingsValidator
from printmate.geometry.loader import load_mesh

router = APIRouter(prefix="/api/settings", tags=["Print Settings"])

@router.get("/printers")
def list_printers():
    """Lists supported printer profiles with kinematics, build volume, and nozzle specs."""
    printers = list(PrinterProfileRegistry._REGISTRY.values())
    return [
        {
            "id": p.id,
            "name": p.name,
            "manufacturer": p.manufacturer,
            "build_volume_mm": [p.build_volume_x, p.build_volume_y, p.build_volume_z],
            "nozzle_diameter_mm": p.default_nozzle_diameter,
            "bed_type": p.default_bed_type,
            "is_default": "a1" in p.id.lower()
        }
        for p in printers
    ]

@router.get("/filaments")
def list_filaments():
    """Lists supported filaments with thermal envelopes, volumetric speeds, and drying specs."""
    filaments = FilamentProfileRegistry.list_filaments()
    return [
        {
            "id": f.id,
            "brand": f.brand,
            "material_name": f.material_name,
            "category": f.category.value,
            "nozzle_temp_range": [f.nozzle_temp_min, f.nozzle_temp_max],
            "bed_temp_range": [f.bed_temp_min, f.bed_temp_max],
            "density_g_cm3": f.density_g_cm3,
            "max_volumetric_speed_mm3_s": f.max_volumetric_speed_mm3_s,
            "requires_enclosure": f.enclosure_required,
            "is_default": "pla_basic" in f.id.lower()
        }
        for f in filaments
    ]

@router.post("/optimize", response_model=PrintSettingsResponse)
def optimize_settings(req: SettingsOptimizeRequest):
    """
    Computes material-aware, printer-aware process parameters, thermals, speeds, and infill.
    Performs instant compatibility validation against physical hardware constraints.
    """
    obj_map = {
        "max_quality": OptimizationObjective.FINE_DETAIL,
        "fine_detail": OptimizationObjective.FINE_DETAIL,
        "balanced_quality": OptimizationObjective.BALANCED_QUALITY,
        "fast_print": OptimizationObjective.FAST_PRINTING,
        "fast_printing": OptimizationObjective.FAST_PRINTING,
        "max_strength": OptimizationObjective.STRONG_FUNCTIONAL,
        "strong_functional": OptimizationObjective.STRONG_FUNCTIONAL,
        "min_support": OptimizationObjective.SUPPORT_MINIMIZED,
        "support_minimized": OptimizationObjective.SUPPORT_MINIMIZED,
    }
    raw_val = req.objective.value if hasattr(req.objective, "value") else str(req.objective)
    obj = obj_map.get(raw_val, OptimizationObjective.BALANCED_QUALITY)

    mesh = None
    if req.model_id:
        jm = JobManager()
        m = jm.get_model(req.model_id)
        if m and os.path.exists(m.get("file_path", "")):
            try:
                mesh = load_mesh(m["file_path"])
            except Exception:
                pass

    settings = SettingsEngine.optimize(
        mesh_or_info=mesh,
        filament_id=req.filament_id,
        printer_id=req.printer_id,
        objective=obj,
        has_connectors=req.has_connectors
    )

    compat = SettingsValidator.validate_settings(settings, req.printer_id, req.filament_id)

    return PrintSettingsResponse(
        printer_name=settings.printer.name,
        filament_name=f"{settings.filament.brand} {settings.filament.material_name}",
        objective=settings.objective.value,
        layer_height_mm=round(settings.layer_height, 2),
        initial_layer_height_mm=round(settings.initial_layer_height, 2),
        wall_loops=settings.wall_loops,
        wall_generator=settings.wall_generator,
        sparse_infill_density=settings.sparse_infill_density,
        sparse_infill_pattern=settings.sparse_infill_pattern,
        top_shell_layers=settings.top_shell_layers,
        bottom_shell_layers=settings.bottom_shell_layers,
        outer_wall_speed_mm_s=settings.outer_wall_speed_mm_s,
        inner_wall_speed_mm_s=settings.inner_wall_speed_mm_s,
        nozzle_temperature=settings.nozzle_temperature,
        bed_temperature=settings.bed_temperature,
        enable_support=settings.enable_support,
        support_type=settings.support_type,
        support_style=settings.support_style,
        support_top_z_gap_mm=round(settings.support_top_z_distance, 2),
        brim_type=settings.brim_type,
        brim_width_mm=round(settings.brim_width_mm, 1),
        estimated_print_time_mins=round(settings.estimated_print_time_mins, 1),
        estimated_filament_grams=round(settings.estimated_filament_grams, 1),
        is_compatible=compat.is_compatible,
        compatibility_errors=compat.errors,
        compatibility_warnings=compat.warnings,
        engineering_rationale=settings.reasoning
    )

