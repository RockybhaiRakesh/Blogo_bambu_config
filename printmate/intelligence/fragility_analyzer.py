"""
Fragility and weak feature analysis module.
Evaluates physical vulnerability of geometric structures (thin protrusions,
narrow necking connections, high aspect-ratio features) without anatomical assumptions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
import trimesh

@dataclass
class FragileFeature:
    """Description of a localized weak geometric region."""
    feature_type: str            # "Thin Protrusion", "Narrow Necking", "Cantilever Extension"
    z_position_mm: float
    effective_diameter_mm: float
    aspect_ratio: float
    description: str

@dataclass
class FragilityReport:
    """Summary of structural fragility risks."""
    total_fragile_features: int
    features: List[FragileFeature] = field(default_factory=list)
    has_critical_necking: bool = False
    has_fragile_protrusions: bool = False
    fragility_risk_score: float = 0.0     # 0.0 (Extremely robust) to 10.0 (Extremely fragile)
    warnings: List[str] = field(default_factory=list)

class FragilityAnalyzer:
    """Identifies geometrically weak and stress-concentrated regions in 3D meshes."""

    @classmethod
    def analyze(
        cls,
        mesh: trimesh.Trimesh,
        num_slices: int = 40,
        critical_diameter_mm: float = 2.5
    ) -> FragilityReport:
        """
        Scans cross-sections across the model height to detect narrow necking,
        thin persistent protrusions, and high aspect-ratio features.

        Args:
            mesh: trimesh.Trimesh instance.
            num_slices: Number of horizontal cross-section slices to analyze.
            critical_diameter_mm: Diameter threshold below which structures are fragile (default 2.5mm).

        Returns:
            FragilityReport dataclass.
        """
        if len(mesh.faces) == 0:
            return FragilityReport(
                total_fragile_features=0,
                warnings=["Empty mesh; fragility analysis skipped."]
            )

        bounds = mesh.bounds
        z_min, z_max = bounds[0][2], bounds[1][2]
        total_height = z_max - z_min

        if total_height < 0.1:
            return FragilityReport(total_fragile_features=0)

        step = total_height / (num_slices + 1)
        slice_z_positions = [z_min + (i + 1) * step for i in range(num_slices)]

        fragile_items: List[FragileFeature] = []
        slice_areas: List[float] = []

        # Analyze cross-sections
        normal = [0.0, 0.0, 1.0]
        for z in slice_z_positions:
            try:
                sec = mesh.section(plane_origin=[0.0, 0.0, z], plane_normal=normal)
                if sec is None:
                    slice_areas.append(0.0)
                    continue

                p2d, _ = sec.to_2D()
                area = float(p2d.area) if hasattr(p2d, 'area') else 0.0
                slice_areas.append(area)

                # Inspect separate polygons on this slice
                polygons = getattr(p2d, 'polygons_full', [])
                if not polygons and hasattr(p2d, 'polygons_closed'):
                    polygons = p2d.polygons_closed

                for poly in polygons:
                    g_area = float(poly.area)
                    if g_area > 0.05:
                        eff_diam = 2.0 * np.sqrt(g_area / np.pi)
                        if eff_diam < critical_diameter_mm:
                            fragile_items.append(FragileFeature(
                                feature_type="Thin Protrusion",
                                z_position_mm=round(float(z), 2),
                                effective_diameter_mm=round(eff_diam, 2),
                                aspect_ratio=round(total_height / max(0.1, eff_diam), 1),
                                description=(
                                    f"Cross-section at Z={z:.1f}mm has effective diameter of {eff_diam:.2f}mm "
                                    f"(< {critical_diameter_mm}mm). Highly susceptible to shear break during support removal."
                                )
                            ))
            except Exception:
                slice_areas.append(0.0)

        # Detect Necking Valley: cross-section area in a valley between larger upper and lower bodies
        has_necking = False
        valid_indices = [i for i, a in enumerate(slice_areas) if a > 0.1]
        if len(valid_indices) >= 5:
            for idx in valid_indices[1:-1]:
                curr_a = slice_areas[idx]
                lower_peak = max(slice_areas[:idx]) if idx > 0 else 0.0
                upper_peak = max(slice_areas[idx + 1:]) if idx < len(slice_areas) - 1 else 0.0

                # Necking occurs if current slice area is less than half of both the upper and lower peak areas
                if curr_a > 0.1 and lower_peak > curr_a * 2.0 and upper_peak > curr_a * 2.0:
                    has_necking = True
                    z_pos = slice_z_positions[idx]
                    eff_d = 2.0 * np.sqrt(curr_a / np.pi)
                    fragile_items.append(FragileFeature(
                        feature_type="Narrow Necking",
                        z_position_mm=round(float(z_pos), 2),
                        effective_diameter_mm=round(eff_d, 2),
                        aspect_ratio=round(min(lower_peak, upper_peak) / max(0.1, curr_a), 1),
                        description=(
                            f"Structural necking at Z={z_pos:.1f}mm (Area = {curr_a:.1f}mm², diam ≈ {eff_d:.1f}mm). "
                            "Stress concentration point; vulnerable to snapping under bending loads."
                        )
                    ))
                    break # Record primary necking zone

        has_protrusions = any(f.feature_type == "Thin Protrusion" for f in fragile_items)
        
        # Fragility score
        score = 0.0
        if has_protrusions:
            score += 4.5
        if has_necking:
            score += 3.5

        # Only apply miniature scale penalty if fragile features actually exist
        if (has_protrusions or has_necking) and total_height < 65.0:
            score += 2.0

        score = min(10.0, round(score, 1))

        warnings: List[str] = []
        if has_protrusions:
            thin_count = sum(1 for f in fragile_items if f.feature_type == "Thin Protrusion")
            warnings.append(
                f"Thin Protrusion Warning: {thin_count} slice instances detected with effective diameter < {critical_diameter_mm}mm. "
                "Enforce 3 wall loops and reduced support contact interface adhesion."
            )
        if has_necking:
            warnings.append(
                "Structural Necking Warning: Model cross-section narrows abruptly between larger masses. "
                "May require split printing or reinforced infill density (>=20%)."
            )

        return FragilityReport(
            total_fragile_features=len(fragile_items),
            features=fragile_items[:20],
            has_critical_necking=has_necking,
            has_fragile_protrusions=has_protrusions,
            fragility_risk_score=score,
            warnings=warnings
        )
