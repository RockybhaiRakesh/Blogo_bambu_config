"""
Overhang analysis module.
Inspects face normals relative to build orientation to identify unsupported downward surfaces,
calculate overhang surface areas, and classify support risks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import trimesh

@dataclass
class OverhangReport:
    """Detailed summary of downward overhang surfaces and support risk."""
    total_surface_area_cm2: float
    total_overhang_area_cm2: float
    overhang_percentage: float
    threshold_angle_deg: float
    safe_area_cm2: float
    moderate_area_cm2: float     # 45 - 60 degrees from vertical
    severe_area_cm2: float       # 60 - 85 degrees from vertical
    horizontal_roof_area_cm2: float # 85 - 90 degrees (pure ceilings)
    high_risk_face_count: int
    high_risk_face_indices: List[int] = field(default_factory=list)
    risk_level: str = "Low"      # "Low", "Moderate", "High", "Critical"
    warnings: List[str] = field(default_factory=list)

class OverhangAnalyzer:
    """Analyzes geometric overhangs relative to gravity / build plate direction."""

    @classmethod
    def analyze(
        cls,
        mesh: trimesh.Trimesh,
        threshold_angle_deg: float = 45.0,
        build_vector: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    ) -> OverhangReport:
        """
        Calculates overhangs across mesh faces relative to the build vector.

        Args:
            mesh: trimesh.Trimesh instance.
            threshold_angle_deg: Angle from vertical beyond which support is needed (default 45°).
            build_vector: Upward normal of the build plate (default (0, 0, 1)).

        Returns:
            OverhangReport dataclass.
        """
        if len(mesh.faces) == 0:
            return OverhangReport(
                total_surface_area_cm2=0.0,
                total_overhang_area_cm2=0.0,
                overhang_percentage=0.0,
                threshold_angle_deg=threshold_angle_deg,
                safe_area_cm2=0.0,
                moderate_area_cm2=0.0,
                severe_area_cm2=0.0,
                horizontal_roof_area_cm2=0.0,
                high_risk_face_count=0,
                risk_level="None",
                warnings=["Empty mesh; overhang analysis skipped."]
            )

        face_normals = mesh.face_normals
        face_areas = mesh.area_faces  # in mm²

        # Normalize build vector
        b_vec = np.array(build_vector, dtype=float)
        b_norm = np.linalg.norm(b_vec)
        if b_norm == 0:
            b_vec = np.array([0.0, 0.0, 1.0])
        else:
            b_vec = b_vec / b_norm

        # Dot product with build vector
        # n_z = face_normal . b_vec
        # n_z > 0: facing upward
        # n_z = 0: vertical wall
        # n_z < 0: facing downward (overhang candidate)
        dots = np.dot(face_normals, b_vec)

        # For downward faces (dots < 0):
        # Angle from vertical wall (0° = vertical wall, 90° = horizontal ceiling facing downward)
        downward_mask = dots < -1e-5
        angles_from_vertical = np.zeros(len(mesh.faces), dtype=float)
        angles_from_vertical[downward_mask] = np.degrees(np.arcsin(np.clip(-dots[downward_mask], 0.0, 1.0)))

        # Categorize areas in mm²
        total_area_mm2 = float(np.sum(face_areas))
        overhang_mask = angles_from_vertical > threshold_angle_deg
        overhang_area_mm2 = float(np.sum(face_areas[overhang_mask]))

        safe_mask = ~overhang_mask
        safe_area_mm2 = float(np.sum(face_areas[safe_mask]))

        moderate_mask = (angles_from_vertical > threshold_angle_deg) & (angles_from_vertical <= 60.0)
        moderate_area_mm2 = float(np.sum(face_areas[moderate_mask]))

        severe_mask = (angles_from_vertical > 60.0) & (angles_from_vertical <= 85.0)
        severe_area_mm2 = float(np.sum(face_areas[severe_mask]))

        horizontal_mask = angles_from_vertical > 85.0
        horizontal_area_mm2 = float(np.sum(face_areas[horizontal_mask]))

        # Convert to cm² (divide by 100)
        total_cm2 = round(total_area_mm2 / 100.0, 2)
        overhang_cm2 = round(overhang_area_mm2 / 100.0, 2)
        safe_cm2 = round(safe_area_mm2 / 100.0, 2)
        moderate_cm2 = round(moderate_area_mm2 / 100.0, 2)
        severe_cm2 = round(severe_area_mm2 / 100.0, 2)
        horizontal_cm2 = round(horizontal_area_mm2 / 100.0, 2)

        overhang_pct = round((overhang_area_mm2 / max(1e-5, total_area_mm2)) * 100.0, 1)

        # High risk faces (severe + horizontal)
        high_risk_indices = np.where(angles_from_vertical > 60.0)[0]
        high_risk_count = len(high_risk_indices)

        # Determine overall support risk level
        if overhang_pct < 2.0 and horizontal_cm2 == 0:
            risk_level = "Low"
        elif overhang_pct < 8.0:
            risk_level = "Moderate"
        elif overhang_pct < 20.0:
            risk_level = "High"
        else:
            risk_level = "Critical"

        warnings: List[str] = []
        if horizontal_cm2 > 0.5:
            warnings.append(
                f"Horizontal Ceilings Detected: {horizontal_cm2:.2f} cm² of surfaces face directly downward (85°-90°). "
                "These require mandatory support structures or will droop into spaghetti."
            )
        if severe_cm2 > 2.0:
            warnings.append(
                f"Severe Overhangs (>60°): {severe_cm2:.2f} cm² require dense support contact. "
                "Tree supports with 0.24mm Z-air gap recommended."
            )
        if overhang_pct > 15.0:
            warnings.append(
                f"Extensive Support Coverage: {overhang_pct:.1f}% of model surface exceeds {threshold_angle_deg}° overhang. "
                "Consider re-orienting model or splitting into 2 parts."
            )

        return OverhangReport(
            total_surface_area_cm2=total_cm2,
            total_overhang_area_cm2=overhang_cm2,
            overhang_percentage=overhang_pct,
            threshold_angle_deg=threshold_angle_deg,
            safe_area_cm2=safe_cm2,
            moderate_area_cm2=moderate_cm2,
            severe_area_cm2=severe_cm2,
            horizontal_roof_area_cm2=horizontal_cm2,
            high_risk_face_count=high_risk_count,
            high_risk_face_indices=high_risk_indices[:100].tolist(),
            risk_level=risk_level,
            warnings=warnings
        )

