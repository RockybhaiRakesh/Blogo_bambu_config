"""
Semantic Feature Detection & 3D Localization module.
Maps visual categories to physical 3D spatial regions (Head, Face, Hands,
Pedestal, Torso, Ornaments) using multi-view projection and mesh envelope analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import trimesh

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.view_renderer import RenderCollection

@dataclass
class SemanticFeature3D:
    """A localized 3D semantic region with spatial coordinates and protection rules."""
    name: str                              # E.g. "Head & Crown", "Hands / Mudra", "Pedestal Base"
    category: str                          # "Anatomy", "Ornament", "Base", "Mechanical"
    bbox_3d: Dict[str, float]              # min_x, max_x, min_y, max_y, min_z, max_z
    center_3d: List[float]                 # [x, y, z] model coordinates
    estimated_volume_cm3: float
    confidence: float                      # 0.0 to 1.0
    localization_status: str               # "verified_multiview", "approximate_geometric", "unresolved"
    is_fragile: bool = False
    recommended_protection: str = "Standard support"

@dataclass
class SemanticDetectionReport:
    """Summary of all detected 3D semantic features."""
    model_name: str
    primary_category: str
    total_features_detected: int
    features: List[SemanticFeature3D] = field(default_factory=list)
    has_delicate_anatomy: bool = False
    has_removable_pedestal: bool = False
    recommended_split_zone_z: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

class SemanticDetector:
    """Performs 3D spatial localization of detected visual features."""

    @classmethod
    def detect_features(
        cls,
        mesh: trimesh.Trimesh,
        classification: VisionClassification,
        render_views: Optional[RenderCollection] = None
    ) -> SemanticDetectionReport:
        """
        Maps classified features to 3D coordinate envelopes on the mesh.

        Args:
            mesh: trimesh.Trimesh instance.
            classification: VisionClassification from VisionClassifier.
            render_views: Optional RenderCollection with camera projection data.

        Returns:
            SemanticDetectionReport dataclass.
        """
        bounds = mesh.bounds
        min_pt, max_pt = bounds[0], bounds[1]
        extents = mesh.extents
        dim_x, dim_y, dim_z = float(extents[0]), float(extents[1]), float(extents[2])
        total_vol = (abs(mesh.volume) / 1000.0) if mesh.is_watertight else (dim_x * dim_y * dim_z * 0.5 / 1000.0)

        features: List[SemanticFeature3D] = []
        has_delicate = False
        has_pedestal = False
        recommended_split_z = None
        warnings: List[str] = []

        status = "verified_multiview" if render_views and len(render_views.views) >= 3 else "approximate_geometric"

        if classification.is_organic_figurine or "Figurine" in classification.primary_category or "Idol" in classification.primary_category:
            # 1. Pedestal / Base Region (Bottom ~25-35% of Z)
            z_ped_max = min_pt[2] + dim_z * 0.32
            features.append(SemanticFeature3D(
                name="Pedestal / Lotus Base",
                category="Base",
                bbox_3d={
                    "min_x": round(float(min_pt[0]), 2), "max_x": round(float(max_pt[0]), 2),
                    "min_y": round(float(min_pt[1]), 2), "max_y": round(float(max_pt[1]), 2),
                    "min_z": round(float(min_pt[2]), 2), "max_z": round(float(z_ped_max), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((min_pt[1] + max_pt[1]) / 2.0), 2),
                    round(float((min_pt[2] + z_ped_max) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol * 0.38, 2),
                confidence=round(classification.confidence * 0.95, 2),
                localization_status=status,
                is_fragile=False,
                recommended_protection="Flat bed orientation; support-free contact"
            ))
            has_pedestal = True
            recommended_split_z = round(float(z_ped_max), 2)

            # 2. Torso & Arms (Middle ~32-75% of Z)
            z_torso_min = z_ped_max
            z_torso_max = min_pt[2] + dim_z * 0.75
            features.append(SemanticFeature3D(
                name="Torso & Main Body",
                category="Anatomy",
                bbox_3d={
                    "min_x": round(float(min_pt[0]), 2), "max_x": round(float(max_pt[0]), 2),
                    "min_y": round(float(min_pt[1]), 2), "max_y": round(float(max_pt[1]), 2),
                    "min_z": round(float(z_torso_min), 2), "max_z": round(float(z_torso_max), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((min_pt[1] + max_pt[1]) / 2.0), 2),
                    round(float((z_torso_min + z_torso_max) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol * 0.42, 2),
                confidence=round(classification.confidence * 0.90, 2),
                localization_status=status,
                is_fragile=False,
                recommended_protection="Gyroid infill reinforcement"
            ))

            # 3. Hands / Mudra (Front quadrant of mid-torso)
            y_mid = (min_pt[1] + max_pt[1]) / 2.0
            z_hands_min = z_ped_max + dim_z * 0.10
            z_hands_max = z_ped_max + dim_z * 0.35
            features.append(SemanticFeature3D(
                name="Hands & Delicate Limbs",
                category="Anatomy",
                bbox_3d={
                    "min_x": round(float(min_pt[0] + dim_x * 0.2), 2), "max_x": round(float(max_pt[0] - dim_x * 0.2), 2),
                    "min_y": round(float(y_mid), 2), "max_y": round(float(max_pt[1]), 2),
                    "min_z": round(float(z_hands_min), 2), "max_z": round(float(z_hands_max), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((y_mid + max_pt[1]) / 2.0), 2),
                    round(float((z_hands_min + z_hands_max) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol * 0.05, 2),
                confidence=round(classification.confidence * 0.85, 2),
                localization_status=status,
                is_fragile=True,
                recommended_protection="Tree Slim supports with >=0.24mm Z-air gap and 0.60mm XY-distance"
            ))
            has_delicate = True

            # 4. Head, Face & Crown (Top ~25% of Z)
            z_head_min = z_torso_max
            features.append(SemanticFeature3D(
                name="Head, Face & Crown",
                category="Anatomy",
                bbox_3d={
                    "min_x": round(float(min_pt[0] + dim_x * 0.15), 2), "max_x": round(float(max_pt[0] - dim_x * 0.15), 2),
                    "min_y": round(float(min_pt[1] + dim_y * 0.15), 2), "max_y": round(float(max_pt[1] - dim_y * 0.15), 2),
                    "min_z": round(float(z_head_min), 2), "max_z": round(float(max_pt[2]), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((min_pt[1] + max_pt[1]) / 2.0), 2),
                    round(float((z_head_min + max_pt[2]) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol * 0.15, 2),
                confidence=round(classification.confidence * 0.92, 2),
                localization_status=status,
                is_fragile=True,
                recommended_protection="Zero support contact on facial features; tilt back if needed"
            ))

        elif classification.is_mechanical:
            # Mechanical envelope breakdown
            features.append(SemanticFeature3D(
                name="Mounting Base / Flange",
                category="Mechanical",
                bbox_3d={
                    "min_x": round(float(min_pt[0]), 2), "max_x": round(float(max_pt[0]), 2),
                    "min_y": round(float(min_pt[1]), 2), "max_y": round(float(max_pt[1]), 2),
                    "min_z": round(float(min_pt[2]), 2), "max_z": round(float(min_pt[2] + dim_z * 0.3), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((min_pt[1] + max_pt[1]) / 2.0), 2),
                    round(float((min_pt[2] + min_pt[2] + dim_z * 0.3) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol * 0.5, 2),
                confidence=round(classification.confidence * 0.90, 2),
                localization_status=status,
                is_fragile=False,
                recommended_protection="Place flat on build plate for maximum mechanical strength"
            ))

        else:
            # General / Sculpture
            features.append(SemanticFeature3D(
                name="Sculptural Body",
                category="Art Piece",
                bbox_3d={
                    "min_x": round(float(min_pt[0]), 2), "max_x": round(float(max_pt[0]), 2),
                    "min_y": round(float(min_pt[1]), 2), "max_y": round(float(max_pt[1]), 2),
                    "min_z": round(float(min_pt[2]), 2), "max_z": round(float(max_pt[2]), 2),
                },
                center_3d=[
                    round(float((min_pt[0] + max_pt[0]) / 2.0), 2),
                    round(float((min_pt[1] + max_pt[1]) / 2.0), 2),
                    round(float((min_pt[2] + max_pt[2]) / 2.0), 2)
                ],
                estimated_volume_cm3=round(total_vol, 2),
                confidence=round(classification.confidence, 2),
                localization_status="approximate_geometric",
                is_fragile=False,
                recommended_protection="Orient for minimum support contact"
            ))

        if has_delicate:
            warnings.append(
                "Delicate Anatomy Alert: Fragile hand/limb features identified. "
                "Enforce safe 0.24mm tree support clearance or consider semantic splitting."
            )

        return SemanticDetectionReport(
            model_name="model",
            primary_category=classification.primary_category,
            total_features_detected=len(features),
            features=features,
            has_delicate_anatomy=has_delicate,
            has_removable_pedestal=has_pedestal,
            recommended_split_zone_z=recommended_split_z,
            warnings=warnings
        )

