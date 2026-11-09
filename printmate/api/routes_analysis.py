"""
Comprehensive Geometry and Vision Analysis Routes.
"""

import os
import time
import threading
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any

_analysis_locks: Dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()

def get_model_lock(model_id: str) -> threading.Lock:
    with _locks_mutex:
        if model_id not in _analysis_locks:
            _analysis_locks[model_id] = threading.Lock()
        return _analysis_locks[model_id]

from printmate.api.schemas import (
    ComprehensiveAnalysisResponse,
    GeometrySummary,
    ThicknessSummary,
    OverhangSummary,
    FragilitySummary,
    IslandSummary,
    SemanticVisionSummary
)
from printmate.api.job_manager import JobManager
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.geometry.loader import load_mesh
from printmate.geometry.thickness_analyzer import ThicknessAnalyzer
from printmate.geometry.overhang_analyzer import OverhangAnalyzer
from printmate.geometry.island_detector import IslandDetector
from printmate.intelligence.fragility_analyzer import FragilityAnalyzer
from printmate.intelligence.classification import ClassificationEngine
from printmate.optimization.orientation_optimizer import OrientationOptimizer
from printmate.vision.vision_classifier import VisionClassifier
from printmate.vision.view_renderer import ViewRenderer

router = APIRouter(prefix="/api/models", tags=["Analysis"])

@router.post("/{model_id}/analyze", response_model=ComprehensiveAnalysisResponse)
def analyze_model(model_id: str):
    """
    Executes Phase 1 geometry intelligence and Phase 2 semantic vision analysis on the model.
    Results are cached in memory for zero-lag subsequent visits.
    Thread-locked to prevent duplicate concurrent runs on the same model.
    """
    jm = JobManager()
    m = jm.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model ID '{model_id}' not found.")

    cached = jm.get_cached_analysis(model_id)
    if cached:
        return ComprehensiveAnalysisResponse(**cached)

    lock = get_model_lock(model_id)
    with lock:
        # Re-check cache inside lock to catch any parallel run that just finished
        cached = jm.get_cached_analysis(model_id)
        if cached:
            return ComprehensiveAnalysisResponse(**cached)

        filepath = m["file_path"]
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Model file not found on disk.")

        t0 = time.time()

        # 1. Geometry Analysis (uses RAM-cached mesh if available for zero disk latency)
        mesh = jm.get_cached_mesh(model_id)
        if mesh is None:
            mesh = load_mesh(filepath)
            jm.set_cached_mesh(model_id, mesh)

        info = GeometryAnalyzer.analyze_mesh(mesh, filepath)
        scale_cat = ClassificationEngine.classify_scale(info)

        # 2. Advanced Physical Printability
        thick_rep = ThicknessAnalyzer.analyze(mesh)
        oh_rep = OverhangAnalyzer.analyze(mesh)
        isl_rep = IslandDetector.analyze(mesh)
        frag_rep = FragilityAnalyzer.analyze(mesh)
        orient_rep = OrientationOptimizer.optimize(mesh)

        # 3. Fast Local Vision Classification (zero network lag, < 10ms)
        renders_dir = os.path.join(os.path.dirname(filepath), "renders")
        os.makedirs(renders_dir, exist_ok=True)
        collection = ViewRenderer.render_views(mesh, output_dir=renders_dir, resolution=(384, 384))
        vis_class = VisionClassifier.classify(collection, provider="local")

        t1 = time.time()

        data = {
            "model_id": model_id,
            "geometry": {
                "dim_x": round(info.dim_x, 2),
                "dim_y": round(info.dim_y, 2),
                "dim_z": round(info.dim_z, 2),
                "faces": info.faces,
                "vertices": info.vertices,
                "volume_cm3": round(info.volume_cm3, 2),
                "surface_area_cm2": round(float(mesh.area) / 100.0, 2) if hasattr(mesh, "area") else 0.0,
                "is_watertight": info.is_watertight,
                "bounds_min": [round(float(x), 2) for x in mesh.bounds[0]],
                "bounds_max": [round(float(x), 2) for x in mesh.bounds[1]],
                "fits_bambu_a1": info.dim_x <= 256.0 and info.dim_y <= 256.0 and info.dim_z <= 256.0,
                "scale_category": scale_cat.category if hasattr(scale_cat, "category") else str(scale_cat)
            },
            "thickness": {
                "min_thickness_mm": round(thick_rep.min_thickness, 2),
                "max_thickness_mm": round(thick_rep.max_thickness, 2),
                "mean_thickness_mm": round(thick_rep.mean_thickness, 2),
                "thin_walls_detected": (thick_rep.critical_samples_count > 0 or thick_rep.min_thickness < 0.8),
                "thin_region_count": thick_rep.critical_samples_count + thick_rep.caution_samples_count,
                "below_nozzle_0_4mm": (thick_rep.critical_samples_count > 0 or thick_rep.min_thickness < 0.40)
            },
            "overhang": {
                "critical_overhang_area_pct": round(oh_rep.overhang_percentage, 1),
                "critical_faces_count": oh_rep.high_risk_face_count,
                "requires_supports": (oh_rep.overhang_percentage > 5.0 or oh_rep.total_overhang_area_cm2 > 2.0),
                "steepest_angle_deg": round(oh_rep.threshold_angle_deg, 1)
            },
            "fragility": {
                "fragility_score": round(frag_rep.fragility_risk_score, 1),
                "fragile_regions_count": len(frag_rep.features),
                "is_delicate_miniature": (frag_rep.fragility_risk_score > 6.0 or frag_rep.has_fragile_protrusions),
                "description": f"Fragility Risk: {frag_rep.fragility_risk_score:.1f}/10 ({len(frag_rep.features)} weak features detected)"
            },
            "islands": {
                "floating_island_count": isl_rep.unsupported_minima_count + isl_rep.disconnected_components_count,
                "has_unsupported_minima": isl_rep.unsupported_minima_count > 0
            },
            "vision": {
                "primary_category": vis_class.primary_category,
                "confidence": round(vis_class.confidence, 2),
                "visual_description": vis_class.visual_description,
                "prominent_features": vis_class.prominent_features,
                "aesthetic_surfaces": vis_class.aesthetic_surfaces,
                "provider_used": vis_class.provider_used
            },
            "recommended_orientations": [
                {
                    "rank": cand.rank,
                    "name": cand.name,
                    "score": round(cand.score, 2),
                    "overhang_area_cm2": round(cand.overhang_area_cm2, 2),
                    "bed_contact_area_cm2": round(cand.bed_contact_area_cm2, 2),
                    "height_mm": round(cand.height_mm, 1),
                    "explanation": cand.explanation
                }
                for cand in orient_rep.top_candidates[:3]
            ],
            "analysis_time_seconds": round(t1 - t0, 2)
        }

        jm.set_cached_analysis(model_id, data)
        return ComprehensiveAnalysisResponse(**data)

@router.get("/{model_id}/analysis", response_model=ComprehensiveAnalysisResponse)
def get_analysis(model_id: str):
    """Retrieves cached analysis results or executes analysis on demand."""
    jm = JobManager()
    cached = jm.get_cached_analysis(model_id)
    if cached:
        return ComprehensiveAnalysisResponse(**cached)
    return analyze_model(model_id)

@router.get("/{model_id}/preview/{view_name}")
def get_view_preview(model_id: str, view_name: str = "isometric"):
    """Serves high-resolution rendered 2D snapshot images for thumbnails and multi-view previews."""
    jm = JobManager()
    m = jm.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found.")

    renders_dir = os.path.join(os.path.dirname(m["file_path"]), "renders")
    img_path = os.path.join(renders_dir, f"{view_name}.png")

    if not os.path.exists(img_path):
        # Generate render on demand
        mesh = load_mesh(m["file_path"])
        ViewRenderer.render_views(mesh, output_dir=renders_dir, resolution=(384, 384))

    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail=f"Preview '{view_name}' could not be rendered.")

