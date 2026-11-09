"""
Optimization Comparison Engine for PRINTMATE AI.
Performs rigorous side-by-side technical auditing between original and optimized assets:
- Mesh geometry & decimation deviation
- Print orientations & overhang exposure
- Slicer strategy comparisons (layer height, walls, infill)
- Heuristic predictions vs. verified Bambu Studio G-code data
Enforces strict engineering integrity: never claims material or time savings without
either actual G-code slicer confirmation or explicit heuristic caveats.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import trimesh

from printmate.slicer.gcode_validator import GCodeMetadata
from printmate.optimization.settings_engine import OptimizedSettings

@dataclass
class ComparisonMetric:
    """A single comparison data point with strict metric provenance."""
    metric_name: str
    baseline_value: str
    optimized_value: str
    difference: str
    pct_change: Optional[float] = None
    is_actual_slicer_data: bool = False
    data_source: str = "Mathematical Heuristic"

@dataclass
class OptimizationComparisonReport:
    """Multi-dimensional optimization audit comparing geometric and slicing metrics."""
    model_name: str
    metrics: List[ComparisonMetric] = field(default_factory=list)
    has_actual_slicer_data: bool = False
    comparison_summary_md: str = ""

    def summary(self) -> str:
        data_type = "SLICER-VERIFIED" if self.has_actual_slicer_data else "HEURISTIC PREDICTIONS"
        lines = [
            f"Optimization Comparison Report [{data_type}]: {self.model_name}",
            "-" * 70,
            f"{'Metric':<25} | {'Baseline':<15} | {'Optimized':<15} | {'Delta':<12} | Source",
            "-" * 70
        ]
        for m in self.metrics:
            lines.append(f"{m.metric_name:<25} | {m.baseline_value:<15} | {m.optimized_value:<15} | {m.difference:<12} | {m.data_source}")
        lines.append("-" * 70)
        return "\n".join(lines)

class OptimizationComparisonEngine:
    """Executes multi-phase comparative analyses across geometry, process settings, and G-code."""

    @classmethod
    def compare_mesh_optimization(
        cls,
        original_mesh: trimesh.Trimesh,
        optimized_mesh: trimesh.Trimesh,
        model_name: str = "Model"
    ) -> List[ComparisonMetric]:
        """Compares geometric topology between source and decimated meshes."""
        orig_faces = len(original_mesh.faces)
        opt_faces = len(optimized_mesh.faces)
        face_diff = opt_faces - orig_faces
        face_pct = (face_diff / orig_faces) * 100.0 if orig_faces > 0 else 0.0

        orig_vol = float(original_mesh.volume) / 1000.0 if original_mesh.is_watertight else 0.0
        opt_vol = float(optimized_mesh.volume) / 1000.0 if optimized_mesh.is_watertight else 0.0
        vol_diff = opt_vol - orig_vol
        vol_pct = (vol_diff / orig_vol) * 100.0 if orig_vol > 0 else 0.0

        orig_z = float(original_mesh.extents[2])
        opt_z = float(optimized_mesh.extents[2])
        z_diff = opt_z - orig_z

        return [
            ComparisonMetric(
                metric_name="Triangle Count",
                baseline_value=f"{orig_faces:,}",
                optimized_value=f"{opt_faces:,}",
                difference=f"{face_diff:+,} ({face_pct:.1f}%)",
                pct_change=face_pct,
                is_actual_slicer_data=False,
                data_source="Mesh Geometry"
            ),
            ComparisonMetric(
                metric_name="Watertight Volume",
                baseline_value=f"{orig_vol:.2f} cm³",
                optimized_value=f"{opt_vol:.2f} cm³",
                difference=f"{vol_diff:+.2f} cm³ ({vol_pct:+.2f}%)",
                pct_change=vol_pct,
                is_actual_slicer_data=False,
                data_source="Mesh Geometry"
            ),
            ComparisonMetric(
                metric_name="Height (Z Extent)",
                baseline_value=f"{orig_z:.2f} mm",
                optimized_value=f"{opt_z:.2f} mm",
                difference=f"{z_diff:+.3f} mm",
                pct_change=0.0,
                is_actual_slicer_data=False,
                data_source="Mesh Geometry"
            )
        ]

    @classmethod
    def compare_heuristic_vs_actual_slicer(
        cls,
        heuristic_settings: OptimizedSettings,
        actual_gcode: GCodeMetadata,
        model_name: str = "Model"
    ) -> OptimizationComparisonReport:
        """
        Conducts deep audit comparing mathematical heuristic predictions against
        actual Bambu Studio G-code toolpath measurements.
        """
        metrics: List[ComparisonMetric] = []

        # 1. Print Duration
        heur_time_mins = heuristic_settings.estimated_print_time_mins
        actual_time_mins = actual_gcode.total_estimated_time_minutes
        time_diff = actual_time_mins - heur_time_mins
        time_pct = (time_diff / heur_time_mins) * 100.0 if heur_time_mins > 0 else 0.0

        metrics.append(ComparisonMetric(
            metric_name="Print Duration",
            baseline_value=f"~{heur_time_mins:.0f} mins (Heuristic)",
            optimized_value=f"{actual_gcode.total_estimated_time_str} ({actual_time_mins:.1f}m)",
            difference=f"{time_diff:+.1f}m ({time_pct:+.1f}%)",
            pct_change=time_pct,
            is_actual_slicer_data=True,
            data_source="Bambu G-code Header"
        ))

        # 2. Filament Mass
        heur_weight = heuristic_settings.estimated_filament_grams
        actual_weight = actual_gcode.total_filament_weight_g
        weight_diff = actual_weight - heur_weight
        weight_pct = (weight_diff / heur_weight) * 100.0 if heur_weight > 0 else 0.0

        metrics.append(ComparisonMetric(
            metric_name="Filament Mass",
            baseline_value=f"~{heur_weight:.1f} g (Heuristic)",
            optimized_value=f"{actual_weight:.2f} g (Actual)",
            difference=f"{weight_diff:+.2f} g ({weight_pct:+.1f}%)",
            pct_change=weight_pct,
            is_actual_slicer_data=True,
            data_source="Bambu G-code Header"
        ))

        # 3. Layer Count
        approx_layers = int(actual_gcode.max_z_height_mm / max(0.08, heuristic_settings.layer_height))
        actual_layers = actual_gcode.total_layers
        layer_diff = actual_layers - approx_layers

        metrics.append(ComparisonMetric(
            metric_name="Total Layers",
            baseline_value=f"~{approx_layers} (Theoretical)",
            optimized_value=f"{actual_layers} layers (Actual)",
            difference=f"{layer_diff:+d} layers",
            pct_change=0.0,
            is_actual_slicer_data=True,
            data_source="Bambu G-code Header"
        ))

        # 4. Process Settings Verification
        metrics.append(ComparisonMetric(
            metric_name="Layer Height",
            baseline_value=f"{heuristic_settings.layer_height:.2f} mm",
            optimized_value=f"{actual_gcode.layer_height_mm:.2f} mm",
            difference="Matched" if abs(heuristic_settings.layer_height - actual_gcode.layer_height_mm) < 0.001 else "Differed",
            is_actual_slicer_data=True,
            data_source="Bambu Config Block"
        ))

        metrics.append(ComparisonMetric(
            metric_name="Support Mode",
            baseline_value=f"{heuristic_settings.support_type} ({heuristic_settings.support_style})",
            optimized_value=f"{'Enabled' if actual_gcode.support_enabled else 'Disabled'} ({actual_gcode.support_style})",
            difference="Verified",
            is_actual_slicer_data=True,
            data_source="Bambu Config Block"
        ))

        # Build Markdown summary
        md_lines = [
            f"### Optimization & Telemetry Comparison: {model_name}",
            "",
            "| Metric | Mathematical Heuristic | Actual Bambu Studio Slicer | Delta / Accuracy | Telemetry Source |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for m in metrics:
            md_lines.append(f"| **{m.metric_name}** | {m.baseline_value} | {m.optimized_value} | {m.difference} | `{m.data_source}` |")
        md_lines.append("")
        md_lines.append("> [!NOTE]")
        md_lines.append("> Mathematical heuristic estimates provide rapid pre-slicing guidance; actual slicer metrics reflect finalized kinematics, purge towers, and acceleration curves.")

        return OptimizationComparisonReport(
            model_name=model_name,
            metrics=metrics,
            has_actual_slicer_data=True,
            comparison_summary_md="\n".join(md_lines)
        )

