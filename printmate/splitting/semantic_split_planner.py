"""
Semantic Split Planner module.
Fuses visual semantic features, physical geometry intelligence (overhangs,
fragility, thickness), and assembly constraints to recommend intelligent print strategies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import trimesh

from printmate.vision.semantic_detector import SemanticDetectionReport
from printmate.geometry.overhang_analyzer import OverhangReport
from printmate.geometry.thickness_analyzer import ThicknessReport
from printmate.intelligence.fragility_analyzer import FragilityReport
from printmate.splitting.split_analyzer import SplitAnalyzer

@dataclass
class SplitStrategyOption:
    """A scored printing strategy candidate."""
    name: str                              # E.g. "Hybrid Semantic Split (Dowel Lock)", "Single Piece Safe Support"
    strategy_type: str                     # "single_piece", "semantic_split", "geometric_split", "hybrid_split"
    score: float                           # 0 - 100
    split_plane_origin: Optional[List[float]] = None
    split_plane_normal: Optional[List[float]] = None
    dowel_connector_feasible: bool = False
    estimated_support_reduction_pct: float = 0.0
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    rationale: str = ""

@dataclass
class SemanticSplitPlan:
    """Comprehensive split recommendation plan."""
    recommended_strategy: SplitStrategyOption
    ranked_options: List[SplitStrategyOption] = field(default_factory=list)
    model_exceeds_bed: bool = False
    best_split_height_z: Optional[float] = None
    assembly_guidance: str = ""
    warnings: List[str] = field(default_factory=list)

class SemanticSplitPlanner:
    """Plans optimal model splitting based on semantic boundaries and physical metrics."""

    BUILD_LIMIT = 256.0

    @classmethod
    def plan(
        cls,
        mesh: trimesh.Trimesh,
        detection_report: SemanticDetectionReport,
        overhang_report: Optional[OverhangReport] = None,
        thickness_report: Optional[ThicknessReport] = None,
        fragility_report: Optional[FragilityReport] = None
    ) -> SemanticSplitPlan:
        """
        Generates and ranks printability and splitting strategies.
        """
        extents = mesh.extents
        dim_x, dim_y, dim_z = float(extents[0]), float(extents[1]), float(extents[2])
        bounds = mesh.bounds
        z_min, z_max = bounds[0][2], bounds[1][2]

        exceeds_bed = (dim_x > cls.BUILD_LIMIT or dim_y > cls.BUILD_LIMIT or dim_z > cls.BUILD_LIMIT)

        options: List[SplitStrategyOption] = []
        warnings: List[str] = []

        # Find best split height Z (waistline or semantic pedestal transition)
        best_z = detection_report.recommended_split_zone_z
        if best_z is None:
            # Fall back to geometric necking analysis
            samples = SplitAnalyzer.sample_cross_sections(mesh, axis=2, num_samples=30)
            candidates = SplitAnalyzer.find_necking_candidates(samples)
            if candidates:
                best_z = float(candidates[0])
            else:
                best_z = float(z_min + dim_z * 0.4)

        # Evaluate cross-sectional area at best_z for dowel connector feasibility
        dowel_feasible = False
        try:
            sec = mesh.section(plane_origin=[0.0, 0.0, best_z], plane_normal=[0.0, 0.0, 1.0])
            if sec is not None:
                p2d, _ = sec.to_2D()
                area = float(p2d.area) if hasattr(p2d, 'area') else 0.0
                # A 6mm dowel pin requires at least ~150 mm² cross-sectional area
                if area >= 150.0:
                    dowel_feasible = True
        except Exception:
            pass

        # -------------------------------------------------------------
        # Option 1: Hybrid Semantic Split (Pedestal + Idol with Dowel Pin)
        # -------------------------------------------------------------
        if not exceeds_bed and detection_report.has_removable_pedestal and dowel_feasible:
            options.append(SplitStrategyOption(
                name="Hybrid Semantic Split with Dowel Pin Lock",
                strategy_type="hybrid_split",
                score=92.0,
                split_plane_origin=[0.0, 0.0, round(best_z, 2)],
                split_plane_normal=[0.0, 0.0, 1.0],
                dowel_connector_feasible=True,
                estimated_support_reduction_pct=65.0,
                pros=[
                    "Pedestal prints flat on bed with zero supports required.",
                    "Separates idol lap from base, eliminating fused support scarring.",
                    "6.0mm male/female dowel pin guarantees perfect alignment and rigid joint.",
                    "Reduces total print time and support filament waste by ~40%."
                ],
                cons=[
                    "Requires 2-part printing and post-print snap/glue assembly.",
                    "Fine seam at pedestal/idol boundary (naturally concealed by lotus petal fold)."
                ],
                rationale=(
                    f"Separating along the natural transition at Z={best_z:.1f}mm isolates the solid base "
                    "from the delicate upper anatomy, allowing both parts to print in their ideal orientations."
                )
            ))

        # -------------------------------------------------------------
        # Option 2: Single-Piece Printing with Safe Tree Supports
        # -------------------------------------------------------------
        if not exceeds_bed:
            single_score = 82.0
            if fragility_report and fragility_report.has_fragile_protrusions:
                single_score -= 10.0  # Risk of breaking delicate hands during removal
            if overhang_report and overhang_report.overhang_percentage > 25.0:
                single_score -= 8.0

            options.append(SplitStrategyOption(
                name="Single-Piece Monolithic with Safe Tree Supports",
                strategy_type="single_piece",
                score=single_score,
                split_plane_origin=None,
                split_plane_normal=None,
                dowel_connector_feasible=False,
                estimated_support_reduction_pct=0.0,
                pros=[
                    "Zero assembly or gluing required; prints as a single complete unit.",
                    "Continuous structural infill from bottom to top.",
                    "Preserves full geometric continuity without any seams."
                ],
                cons=[
                    "Requires tree supports under delicate hands and chin.",
                    "Risk of breaking thin appendages during support removal if air-gap is inadequate.",
                    "Longer print time and higher filament usage."
                ],
                rationale=(
                    "Ideal for users who prefer zero post-processing assembly. Requires strict enforcement "
                    "of 0.24mm Z-distance and 0.60mm XY-clearance to protect fine details."
                )
            ))

        # -------------------------------------------------------------
        # Option 3: Pure Geometric Bisecting Split
        # -------------------------------------------------------------
        options.append(SplitStrategyOption(
            name="Planar Geometric Midpoint Split",
            strategy_type="geometric_split",
            score=70.0 if not exceeds_bed else 95.0,
            split_plane_origin=[0.0, 0.0, round(float(z_min + dim_z * 0.5), 2)],
            split_plane_normal=[0.0, 0.0, 1.0],
            dowel_connector_feasible=dowel_feasible,
            estimated_support_reduction_pct=45.0,
            pros=[
                "Enables printing models that exceed the 256mm build volume.",
                "Reduces height-to-base tipping risk on tall narrow objects."
            ],
            cons=[
                "Bisects geometry across mid-torso, creating an arbitrary visible horizontal seam.",
                "Requires careful dowel alignment and sanding."
            ],
            rationale=(
                "Mandatory when model exceeds 256mm build envelope; secondary fallback for standard models."
            )
        ))

        # Sort descending by score
        options.sort(key=lambda o: o.score, reverse=True)

        recommended = options[0]

        assembly_guide = (
            "Assembly Guidance: For split printing with dowel connectors, clean internal socket relief with a 6.5mm drill bit "
            "if needed. Use cyanoacrylate (superglue) or epoxy for permanent mechanical bonding."
        )

        return SemanticSplitPlan(
            recommended_strategy=recommended,
            ranked_options=options,
            model_exceeds_bed=exceeds_bed,
            best_split_height_z=best_z,
            assembly_guidance=assembly_guide,
            warnings=warnings
        )

