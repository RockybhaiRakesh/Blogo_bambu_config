"""
Analysis report generator module.
Formats comprehensive Phase 1 geometry intelligence: dimensions, integrity,
wall thickness, overhangs, floating islands, fragility, and optimal orientations.
"""

import os
from typing import List, Optional, Dict, Any
from printmate.core.models import ModelInfo
from printmate.geometry.thickness_analyzer import ThicknessReport
from printmate.geometry.overhang_analyzer import OverhangReport
from printmate.geometry.island_detector import IslandReport
from printmate.intelligence.fragility_analyzer import FragilityReport
from printmate.optimization.orientation_optimizer import OrientationReport

class AnalysisReporter:
    """Produces standardized diagnostic reports for models and slicing workflows."""

    @staticmethod
    def format_console_summary(
        info: ModelInfo,
        risks: List[str],
        scale_class: str,
        project_path: Optional[str] = None,
        thickness_report: Optional[ThicknessReport] = None,
        overhang_report: Optional[OverhangReport] = None,
        island_report: Optional[IslandReport] = None,
        fragility_report: Optional[FragilityReport] = None,
        orientation_report: Optional[OrientationReport] = None
    ) -> str:
        """
        Formats a clean ASCII terminal summary including Phase 1 metrics.
        """
        lines = [
            "=" * 68,
            f" PRINTMATE AI - ADVANCED GEOMETRY INTELLIGENCE REPORT",
            "=" * 68,
            f" File: {info.filename}",
            f" Dimensions (X x Y x Z): {info.dim_x:.2f} x {info.dim_y:.2f} x {info.dim_z:.2f} mm",
            f" Build Plate Fit (256mm³): {'Fits [OK]' if info.fits_a1_bed else 'EXCEEDS A1 BED [!]'}",
            f" Poly Count: {info.faces:,} faces ({info.vertices:,} vertices)",
            f" Watertight: {'Yes [OK]' if info.is_watertight else 'No (Needs Repair) [!] '}",
            f" Scale Tier: {scale_class}",
            "-" * 68,
        ]

        # Wall Thickness
        if thickness_report:
            lines.extend([
                f" WALL THICKNESS ANALYSIS (Samples: {thickness_report.samples_evaluated}):",
                f"   - Min / Mean / Max: {thickness_report.min_thickness:.2f} mm / {thickness_report.mean_thickness:.2f} mm / {thickness_report.max_thickness:.2f} mm",
                f"   - Sub-0.4mm Critical Samples: {thickness_report.critical_samples_count}",
                f"   - 0.4 - 0.8mm Caution Samples: {thickness_report.caution_samples_count}",
                "-" * 68
            ])

        # Overhangs
        if overhang_report:
            lines.extend([
                f" OVERHANG & SUPPORT PROFILE (Threshold: {overhang_report.threshold_angle_deg}°):",
                f"   - Overhang Area: {overhang_report.total_overhang_area_cm2:.2f} cm² ({overhang_report.overhang_percentage:.1f}%)",
                f"   - Severe Overhangs (>60°): {overhang_report.severe_area_cm2:.2f} cm²",
                f"   - Downward Ceilings (85-90°): {overhang_report.horizontal_roof_area_cm2:.2f} cm²",
                f"   - Overall Support Risk: {overhang_report.risk_level}",
                "-" * 68
            ])

        # Floating Islands
        if island_report:
            lines.extend([
                f" ISLAND & TOPOLOGY DETECTOR:",
                f"   - Disconnected Bodies: {island_report.disconnected_components_count}",
                f"   - Mid-Air Island Seeds: {island_report.unsupported_minima_count} "
                f"({island_report.island_over_model_count} over model, {island_report.island_over_bed_count} over bed)",
                "-" * 68
            ])

        # Fragile Features
        if fragility_report:
            lines.extend([
                f" GEOMETRIC FRAGILITY ANALYSIS:",
                f"   - Vulnerability Score: {fragility_report.fragility_risk_score:.1f} / 10.0",
                f"   - Thin Protrusions Detected: {'Yes' if fragility_report.has_fragile_protrusions else 'None'}",
                f"   - Structural Necking Detected: {'Yes' if fragility_report.has_critical_necking else 'None'}",
                "-" * 68
            ])

        # Orientations
        if orientation_report and orientation_report.top_candidates:
            lines.extend([
                f" CANDIDATE ORIENTATIONS (Top {len(orientation_report.top_candidates)}):"
            ])
            for c in orientation_report.top_candidates:
                lines.append(
                    f"   [{c.rank}] {c.name} - Score: {c.score:.1f} | Overhang: {c.overhang_area_cm2:.1f}cm² | Bed Contact: {c.bed_contact_area_cm2:.1f}cm²"
                )
            lines.append("-" * 68)

        # Risks
        all_warnings: List[str] = list(risks)
        if thickness_report:
            all_warnings.extend(thickness_report.warnings)
        if overhang_report:
            all_warnings.extend(overhang_report.warnings)
        if island_report:
            all_warnings.extend(island_report.warnings)
        if fragility_report:
            all_warnings.extend(fragility_report.warnings)

        lines.append(f" COMBINED PRINTABILITY WARNINGS ({len(all_warnings)} items):")
        if not all_warnings:
            lines.append("   [OK] Model exhibits zero critical geometric hazards.")
        else:
            for w in all_warnings[:8]:  # Top 8 in console
                lines.append(f"   [!] {w}")

        if project_path:
            lines.extend([
                "-" * 68,
                f" Slicer Project: {os.path.basename(project_path)}",
                f" Status: Ready for Bambu Studio [OK]"
            ])

        lines.append("=" * 68)
        return "\n".join(lines)

    @staticmethod
    def generate_markdown_report(
        info: ModelInfo,
        risks: List[str],
        scale_class: str,
        project_path: Optional[str] = None,
        output_file: Optional[str] = None,
        thickness_report: Optional[ThicknessReport] = None,
        overhang_report: Optional[OverhangReport] = None,
        island_report: Optional[IslandReport] = None,
        fragility_report: Optional[FragilityReport] = None,
        orientation_report: Optional[OrientationReport] = None
    ) -> str:
        """
        Generates a comprehensive 12-section Phase 1 markdown report.
        """
        lines = [
            f"# PrintMate AI – Comprehensive Printability Intelligence Report",
            f"**Model File:** `{info.filename}`  ",
            f"**Target Hardware:** Bambu Lab A1 (0.4mm Nozzle, 256x256x256mm)  ",
            "",
            "---",
            "",
            "## 1. Model Dimensions & Bounding Envelope",
            f"- **Extents:** `{info.dim_x:.2f} mm` (X) x `{info.dim_y:.2f} mm` (Y) x `{info.dim_z:.2f} mm` (Z / Height)",
            f"- **Volume:** `{info.volume_cm3:.2f} cm³`",
            f"- **Scale Tier:** `{scale_class}`",
            "",
            "## 2. Mesh Integrity & Watertightness",
            f"- **Polygons:** `{info.faces:,}` triangles ({info.vertices:,} vertices)",
            f"- **Watertight Status:** `{'Watertight Manifold [OK]' if info.is_watertight else 'Open / Non-Manifold Boundaries [!]'}`",
            "",
            "## 3. Wall Thickness Statistics (Ray-Sampled)",
        ]

        if thickness_report:
            lines.extend([
                f"- **Evaluated Samples:** `{thickness_report.samples_evaluated}` ray intersections",
                f"- **Minimum Wall Thickness:** `{thickness_report.min_thickness:.2f} mm`",
                f"- **Mean Wall Thickness:** `{thickness_report.mean_thickness:.2f} mm`",
                f"- **Maximum Wall Thickness:** `{thickness_report.max_thickness:.2f} mm`",
                "",
                "## 4. Thin-Wall & Sub-Perimeter Warnings",
                f"- **Critical Below-Nozzle Features (<0.40mm):** `{thickness_report.critical_samples_count}` instances",
                f"- **Caution Sub-Perimeter Features (0.40 - 0.80mm):** `{thickness_report.caution_samples_count}` instances",
            ])
            for w in thickness_report.warnings:
                lines.append(f"  - ⚠️ {w}")
        else:
            lines.append("- *Thickness analysis was not executed for this run.*")

        lines.extend([
            "",
            "## 5. Overhang Profile & Support Regions",
        ])
        if overhang_report:
            lines.extend([
                f"- **Total Surface Area:** `{overhang_report.total_surface_area_cm2:.2f} cm²`",
                f"- **Overhang Area (>45°):** `{overhang_report.total_overhang_area_cm2:.2f} cm²` ({overhang_report.overhang_percentage:.1f}%)",
                f"- **Severe Overhang Area (>60°):** `{overhang_report.severe_area_cm2:.2f} cm²`",
                f"- **Downward Horizontal Ceilings (85°-90°):** `{overhang_report.horizontal_roof_area_cm2:.2f} cm²`",
                f"- **Support Risk Classification:** `{overhang_report.risk_level}`",
            ])
            for w in overhang_report.warnings:
                lines.append(f"  - ⚠️ {w}")
        else:
            lines.append("- *Overhang analysis was not executed for this run.*")

        lines.extend([
            "",
            "## 6. Floating Island & Topology Analysis",
        ])
        if island_report:
            lines.extend([
                f"- **Disconnected Solid Bodies:** `{island_report.disconnected_components_count}`",
                f"- **Loose Debris Detected:** `{'Yes' if island_report.has_disconnected_debris else 'No'}`",
                f"- **Mid-Air Island Seeds (Local Z-Minima):** `{island_report.unsupported_minima_count}`",
                f"  - Overhanging Model Body: `{island_report.island_over_model_count}`",
                f"  - Overhanging Build Plate: `{island_report.island_over_bed_count}`",
            ])
            for w in island_report.warnings:
                lines.append(f"  - ⚠️ {w}")
        else:
            lines.append("- *Island detection was not executed for this run.*")

        lines.extend([
            "",
            "## 7. Geometric Fragility & Stress Concentrations",
        ])
        if fragility_report:
            lines.extend([
                f"- **Fragility Risk Score:** `{fragility_report.fragility_risk_score:.1f} / 10.0`",
                f"- **Identified Fragile Features:** `{fragility_report.total_fragile_features}`",
                f"- **Structural Necking Notches:** `{'Detected [!]' if fragility_report.has_critical_necking else 'None'}`",
                f"- **Thin Protrusions (<2.5mm):** `{'Detected [!]' if fragility_report.has_fragile_protrusions else 'None'}`",
            ])
            for f_item in fragility_report.features[:5]:
                lines.append(f"  - *{f_item.feature_type}* at Z={f_item.z_position_mm}mm (Diam ≈ {f_item.effective_diameter_mm}mm)")
        else:
            lines.append("- *Fragility analysis was not executed for this run.*")

        lines.extend([
            "",
            "## 8. Orientation Evaluation (Top 3 Candidates)",
        ])
        if orientation_report and orientation_report.top_candidates:
            for cand in orientation_report.top_candidates:
                lines.extend([
                    f"### Rank {cand.rank}: {cand.name} (Score: {cand.score:.1f}/100)",
                    f"- **Bed Contact Area:** `{cand.bed_contact_area_cm2:.2f} cm²`",
                    f"- **Overhang Area:** `{cand.overhang_area_cm2:.2f} cm²`",
                    f"- **Estimated Support Volume:** `{cand.estimated_support_volume_cm3:.2f} cm³`",
                    f"- **Z Height:** `{cand.height_mm:.1f} mm`",
                    f"- **Assessment:** {cand.explanation}",
                    ""
                ])
        else:
            lines.append("- *Orientation optimization was not executed for this run.*")

        lines.extend([
            "## 9. Build Plate Fit Verification",
            f"- **Bambu Lab A1 Envelope:** `256 x 256 x 256 mm`",
            f"- **Bed Clearance:** `{'FITS CONFIRMED [OK]' if info.fits_a1_bed else 'OVERSIZED - EXCEEDS BUILD VOLUME [!]'}`",
            "",
            "## 10. Combined Printability Risk Assessment",
        ])
        all_warnings: List[str] = list(risks)
        if thickness_report: all_warnings.extend(thickness_report.warnings)
        if overhang_report: all_warnings.extend(overhang_report.warnings)
        if island_report: all_warnings.extend(island_report.warnings)
        if fragility_report: all_warnings.extend(fragility_report.warnings)

        if not all_warnings:
            lines.append("- Model satisfies all FDM printability safety parameters without severe risks.")
        else:
            for w in all_warnings:
                lines.append(f"- **Risk:** {w}")

        lines.extend([
            "",
            "## 11. Recommended Print Strategy",
            "- **Nozzle / Extrusion:** `0.40mm nozzle` with `Arachne` perimeter generator.",
            "- **Layer Height:** `0.12mm` for miniature and high-detail surfaces.",
            "- **Wall Loops:** `3 perimeters` minimum to reinforce delicate protrusions.",
            "- **Support Configuration:** `Tree Slim (auto)` with `0.24mm top Z-air gap` and `0.60mm XY-distance` to prevent support fusion.",
            "- **Infill:** `15% Gyroid` for multidirectional tensile strength without infill nozzle grinding.",
            "",
            "## 12. Unresolved Analysis Limitations",
            "- **No Semantic Recognition:** Features are analyzed via pure differential geometry (normals, ray-casts, cross-sections). Anatomical recognition (hands, eyes, jewelry) is reserved for Phase 2 vision models.",
            "- **Slicer Toolpath Discretization:** Ray sampling approximates continuous geometry; actual slicer perimeter extrusion is subject to layer discretization slicing artifacts.",
            "- **Material Shrinkage & Thermal Warping:** Linear expansion/contraction coefficients for high-temperature filaments (ABS, Nylon) are not modeled (target machine is Bambu A1 open-bed with PLA/PETG).",
            ""
        ])

        if project_path:
            lines.extend([
                "---",
                "## Project Generation Status",
                f"- **Project File:** `{project_path}`",
                "- **Status:** Ready for Bambu Studio [OK]"
            ])

        content = "\n".join(lines)
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return content
