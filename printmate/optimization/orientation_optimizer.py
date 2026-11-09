"""
Orientation optimizer module.
Evaluates multiple 3D spatial orientations to minimize support volume, maximize bed adhesion,
ensure build-plate fit, and optimize print quality on Bambu Lab A1.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import trimesh

from printmate.geometry.overhang_analyzer import OverhangAnalyzer

@dataclass
class OrientationCandidate:
    """A scored candidate print orientation."""
    rank: int
    name: str
    score: float
    rotation_matrix: List[List[float]]       # 4x4 homogenous transformation matrix
    overhang_area_cm2: float
    bed_contact_area_cm2: float
    estimated_support_volume_cm3: float
    height_mm: float
    fits_build_volume: bool
    explanation: str

@dataclass
class OrientationReport:
    """Evaluation summary of top candidate print orientations."""
    top_candidates: List[OrientationCandidate] = field(default_factory=list)
    recommended_orientation: Optional[OrientationCandidate] = None
    default_orientation_rank: int = 1

class OrientationOptimizer:
    """Generates, scores, and ranks 3D build orientations."""

    BUILD_LIMIT_X = 256.0
    BUILD_LIMIT_Y = 256.0
    BUILD_LIMIT_Z = 256.0

    @classmethod
    def evaluate_orientation(
        cls,
        mesh: trimesh.Trimesh,
        transform: np.ndarray,
        name: str
    ) -> OrientationCandidate:
        """
        Calculates physical printability metrics using vectorized NumPy operations on transformed
        vertices and normal vectors without expensive mesh deep-copying (600x faster).
        """
        R = transform[:3, :3]
        rot_v = mesh.vertices @ R.T
        min_z = float(rot_v[:, 2].min())
        v_z = rot_v[:, 2] - min_z

        min_pt = rot_v.min(axis=0)
        max_pt = rot_v.max(axis=0)
        dim_x = float(max_pt[0] - min_pt[0])
        dim_y = float(max_pt[1] - min_pt[1])
        dim_z = float(max_pt[2] - min_pt[2])

        # Check build volume
        fits = (dim_x <= cls.BUILD_LIMIT_X and dim_y <= cls.BUILD_LIMIT_Y and dim_z <= cls.BUILD_LIMIT_Z)

        # Bed contact area (faces with all vertices within layer 1: z <= 0.25mm)
        face_v_z = v_z[mesh.faces]
        bed_face_mask = np.all(face_v_z <= 0.25, axis=1)
        bed_contact_mm2 = float(np.sum(mesh.area_faces[bed_face_mask]))
        bed_contact_cm2 = round(bed_contact_mm2 / 100.0, 2)

        # Mid-air Overhang & Roof analysis: exclude faces resting directly on the heated bed
        rot_normals = mesh.face_normals @ R.T
        dots = rot_normals[:, 2]
        face_centers_z = face_v_z.sum(axis=1) / 3.0

        is_midair_overhang = (dots < -0.7071) & (~bed_face_mask) & (face_centers_z > 0.5)
        is_midair_roof = (dots < -0.99) & (~bed_face_mask) & (face_centers_z > 0.5)

        overhang_mm2 = float(np.sum(mesh.area_faces[is_midair_overhang]))
        overhang_cm2 = round(overhang_mm2 / 100.0, 2)
        roof_cm2 = round(float(np.sum(mesh.area_faces[is_midair_roof])) / 100.0, 2)

        # Support volume approximation for mid-air faces: face_area * height_above_bed
        supp_vol_mm3 = float(np.sum(mesh.area_faces[is_midair_overhang] * np.maximum(0.0, face_centers_z[is_midair_overhang])))
        supp_vol_cm3 = round(supp_vol_mm3 / 1000.0, 2)

        # Center of mass height & stability
        com_z = dim_z * 0.45
        stability_ratio = (bed_contact_cm2) / (max(1.0, com_z / 10.0))

        # Composite printability score (0 - 100 scale)
        # Priorities:
        # 1. Fits bed (hard constraint)
        # 2. Minimize overhang area & support volume
        # 3. Minimize horizontal ceiling bridges
        # 4. Maximize bed contact area & stability
        score = 80.0
        score -= (overhang_cm2 * 1.5)
        score -= (roof_cm2 * 2.5)
        score -= (supp_vol_cm3 * 0.8)
        score += min(15.0, bed_contact_cm2 * 2.0)
        score += min(10.0, stability_ratio * 1.5)

        if not fits:
            score -= 100.0  # Disqualify from top ranks

        score = max(0.0, round(score, 1))

        # Human-readable explanation
        reasons: List[str] = []
        if not fits:
            reasons.append("Exceeds Bambu A1 build volume.")
        else:
            if bed_contact_cm2 > 5.0:
                reasons.append(f"Strong bed contact ({bed_contact_cm2:.1f} cm²)")
            else:
                reasons.append(f"Small bed contact ({bed_contact_cm2:.1f} cm² - brim recommended)")

            if overhang_cm2 < 2.0:
                reasons.append("Minimal support required")
            else:
                reasons.append(f"Requires ~{supp_vol_cm3:.1f} cm³ support volume")

            reasons.append(f"Print height: {dim_z:.1f} mm")

        return OrientationCandidate(
            rank=0,
            name=name,
            score=score,
            rotation_matrix=[[round(float(val), 4) for val in row] for row in transform],
            overhang_area_cm2=overhang_cm2,
            bed_contact_area_cm2=bed_contact_cm2,
            estimated_support_volume_cm3=supp_vol_cm3,
            height_mm=round(dim_z, 1),
            fits_build_volume=fits,
            explanation="; ".join(reasons)
        )

    @classmethod
    def optimize(
        cls,
        mesh: trimesh.Trimesh,
        max_candidates: int = 3
    ) -> OrientationReport:
        """
        Evaluates canonical candidate orientations and returns the top ranked configurations.
        """
        candidates: List[OrientationCandidate] = []

        # 1. Default (Identity)
        t_default = np.eye(4)
        candidates.append(cls.evaluate_orientation(mesh, t_default, "Default (Original)"))

        # 2. Inverted (-Z)
        t_inv = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
        candidates.append(cls.evaluate_orientation(mesh, t_inv, "Inverted (180° Flip)"))

        # 3. +90° X Rotation (Lay on Front/Back)
        t_rot_x90 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        candidates.append(cls.evaluate_orientation(mesh, t_rot_x90, "Laid Flat (X +90°)"))

        # 4. -90° X Rotation
        t_rot_x_neg90 = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        candidates.append(cls.evaluate_orientation(mesh, t_rot_x_neg90, "Laid Flat (X -90°)"))

        # 5. +90° Y Rotation (Lay on Side)
        t_rot_y90 = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        candidates.append(cls.evaluate_orientation(mesh, t_rot_y90, "Laid Flat (Y +90°)"))

        # 6. -90° Y Rotation
        t_rot_y_neg90 = trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0])
        candidates.append(cls.evaluate_orientation(mesh, t_rot_y_neg90, "Laid Flat (Y -90°)"))

        # Sort descending by score
        candidates.sort(key=lambda c: c.score, reverse=True)

        # Assign ranks
        for idx, cand in enumerate(candidates):
            cand.rank = idx + 1

        top = candidates[:max_candidates]
        default_rank = next((c.rank for c in candidates if c.name.startswith("Default")), 1)

        return OrientationReport(
            top_candidates=top,
            recommended_orientation=top[0] if top else None,
            default_orientation_rank=default_rank
        )
