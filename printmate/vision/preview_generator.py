"""
Interactive Preview Data Generator module.
Formats multi-view image sets, semantic region overlays, candidate split planes,
and confidence metrics into structured JSON and annotated PNGs for UI integration.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from PIL import Image, ImageDraw, ImageFont

from printmate.core.config import Config
from printmate.vision.view_renderer import RenderCollection
from printmate.vision.semantic_detector import SemanticDetectionReport
from printmate.vision.semantic_segmenter import SegmentedMesh

if TYPE_CHECKING:
    from printmate.splitting.semantic_split_planner import SemanticSplitPlan
    from printmate.intelligence.decision_engine import StrategicPrintPlan

@dataclass
class UIPreviewPayload:
    """Structured data package for React / Web UI model viewer."""
    model_name: str
    manifest_path: str
    view_images: Dict[str, str]
    annotated_overlay_path: Optional[str]
    semantic_parts: List[Dict[str, Any]]
    candidate_split_planes: List[Dict[str, Any]]
    recommended_strategy: str
    overall_confidence: float
    user_decision_required: bool
    user_questions: List[Dict[str, Any]]

class PreviewGenerator:
    """Generates preview snapshots, visual bounding box overlays, and UI manifests."""

    @classmethod
    def generate_ui_preview(
        cls,
        model_name: str,
        render_collection: RenderCollection,
        semantic_report: SemanticDetectionReport,
        segmented_mesh: SegmentedMesh,
        split_plan: Any,
        decision_plan: Any,
        output_dir: Optional[str] = None
    ) -> UIPreviewPayload:
        """
        Builds the complete visual package and JSON manifest.
        """
        target_dir = output_dir or os.path.join(Config.WORKSPACE_DIR, "outputs", "previews", model_name)
        os.makedirs(target_dir, exist_ok=True)

        view_paths: Dict[str, str] = {}
        for v_name, v_info in render_collection.views.items():
            view_paths[v_name] = v_info.image_path

        # 1. Generate annotated 2D overlay on the front view if available
        overlay_path = None
        front_view = render_collection.get_view("front") or render_collection.get_view("isometric")
        if front_view and os.path.exists(front_view.image_path):
            overlay_path = cls._create_annotated_overlay(
                image_path=front_view.image_path,
                semantic_report=semantic_report,
                segmented_mesh=segmented_mesh,
                split_plan=split_plan,
                out_path=os.path.join(target_dir, f"{model_name}_semantic_overlay.png")
            )

        # 2. Package semantic parts data
        parts: List[Dict[str, Any]] = []
        for feat in semantic_report.features:
            color = segmented_mesh.visual_color_palette.get(feat.name, [150, 150, 150, 255])
            parts.append({
                "name": feat.name,
                "category": feat.category,
                "confidence": feat.confidence,
                "is_fragile": feat.is_fragile,
                "protection_rule": feat.recommended_protection,
                "bbox_3d": feat.bbox_3d,
                "center_3d": feat.center_3d,
                "color_rgba": color,
                "face_count": segmented_mesh.face_counts_per_feature.get(feat.name, 0)
            })

        # 3. Package split planes
        split_planes: List[Dict[str, Any]] = []
        for opt in split_plan.ranked_options:
            if opt.split_plane_origin:
                split_planes.append({
                    "strategy_name": opt.name,
                    "height_z_mm": opt.split_plane_origin[2],
                    "plane_normal": opt.split_plane_normal,
                    "dowel_lock_feasible": opt.dowel_connector_feasible,
                    "support_reduction": f"{opt.estimated_support_reduction_pct:.0f}%",
                    "pros": opt.pros,
                    "cons": opt.cons
                })

        # 4. Package questions
        questions: List[Dict[str, Any]] = []
        for q in decision_plan.pending_questions:
            questions.append({
                "question_id": q.question_id,
                "prompt": q.prompt,
                "options": q.options,
                "recommended_option": q.recommended_option,
                "reason": q.reason
            })

        manifest = {
            "model_name": model_name,
            "recommended_strategy": decision_plan.selected_strategy_name,
            "overall_confidence": decision_plan.confidence,
            "user_decision_required": decision_plan.user_decision_required,
            "views": view_paths,
            "annotated_overlay": overlay_path,
            "semantic_parts": parts,
            "candidate_split_planes": split_planes,
            "user_questions": questions
        }

        manifest_file = os.path.join(target_dir, "preview_manifest.json")
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        return UIPreviewPayload(
            model_name=model_name,
            manifest_path=manifest_file,
            view_images=view_paths,
            annotated_overlay_path=overlay_path,
            semantic_parts=parts,
            candidate_split_planes=split_planes,
            recommended_strategy=decision_plan.selected_strategy_name,
            overall_confidence=decision_plan.confidence,
            user_decision_required=decision_plan.user_decision_required,
            user_questions=questions
        )

    @classmethod
    def _create_annotated_overlay(
        cls,
        image_path: str,
        semantic_report: SemanticDetectionReport,
        segmented_mesh: SegmentedMesh,
        split_plan: Any,
        out_path: str
    ) -> str:
        """Draws visual semantic boundary lines and split plane indicators on a 2D snapshot."""
        try:
            im = Image.open(image_path).convert("RGBA")
            overlay = Image.new("RGBA", im.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            w, h = im.size

            # Draw candidate split plane line if defined
            if split_plan.best_split_height_z is not None:
                # Approximate 2D height line at lower third (y corresponds to inverted Z)
                split_y = int(h * 0.68)
                draw.line([(20, split_y), (w - 20, split_y)], fill=(255, 60, 60, 220), width=3)
                draw.text((30, split_y - 18), "RECOMMENDED SPLIT PLANE (Lotus Pedestal Transition)", fill=(255, 40, 40, 255))

            # Composite and save
            combined = Image.alpha_composite(im, overlay)
            combined.save(out_path, "PNG")
            return out_path
        except Exception:
            return image_path
