"""
Unit tests for Optimization Comparison Engine (OptimizationComparisonEngine).
"""

import os
import unittest
import trimesh

from printmate.optimization.comparison_engine import (
    OptimizationComparisonEngine,
    OptimizationComparisonReport,
    ComparisonMetric
)
from printmate.optimization.settings_engine import SettingsEngine, OptimizationObjective
from printmate.slicer.gcode_validator import GCodeValidator

class TestOptimizationComparisonEngine(unittest.TestCase):

    REAL_GCODE = "outputs/gcode/single_color_PLA_2h20m.gcode"

    def test_mesh_topology_comparison(self):
        """Verifies geometric topology difference reporting between original and decimated box."""
        box1 = trimesh.creation.box(extents=[20, 20, 20])
        box2 = trimesh.creation.box(extents=[20, 20, 20])
        metrics = OptimizationComparisonEngine.compare_mesh_optimization(box1, box2, "Box")

        self.assertIsInstance(metrics, list)
        self.assertEqual(len(metrics), 3)
        tri_m = next(m for m in metrics if m.metric_name == "Triangle Count")
        self.assertFalse(tri_m.is_actual_slicer_data)
        self.assertEqual(tri_m.data_source, "Mesh Geometry")

    def test_heuristic_vs_actual_slicer_comparison(self):
        """Verifies side-by-side comparison between heuristic estimations and real Bambu Studio G-code."""
        if not os.path.exists(self.REAL_GCODE):
            self.skipTest("Real G-code file not present.")

        gcode_res = GCodeValidator.validate_gcode(self.REAL_GCODE)
        self.assertTrue(gcode_res.is_valid)

        # Generate heuristic settings for a 55mm model
        box = trimesh.creation.box(extents=[30, 30, 55])
        settings = SettingsEngine.optimize(box, objective=OptimizationObjective.FINE_DETAIL)

        report = OptimizationComparisonEngine.compare_heuristic_vs_actual_slicer(
            heuristic_settings=settings,
            actual_gcode=gcode_res.metadata,
            model_name="single_color.stl"
        )

        self.assertIsInstance(report, OptimizationComparisonReport)
        self.assertTrue(report.has_actual_slicer_data)
        self.assertEqual(report.model_name, "single_color.stl")
        self.assertIn("Print Duration", [m.metric_name for m in report.metrics])
        self.assertIn("Filament Mass", [m.metric_name for m in report.metrics])

        time_m = next(m for m in report.metrics if m.metric_name == "Print Duration")
        self.assertTrue(time_m.is_actual_slicer_data)
        self.assertIn("Bambu G-code", time_m.data_source)

        # Verify Markdown summary contains table
        self.assertIn("| Metric | Mathematical Heuristic |", report.comparison_summary_md)
        self.assertIn("Bambu Studio Slicer", report.comparison_summary_md)

if __name__ == "__main__":
    unittest.main()

