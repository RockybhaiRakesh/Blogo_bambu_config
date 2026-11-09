"""
Unit tests for PrintMate geometric fragility analyzer.
"""

import unittest
import numpy as np
import trimesh

from printmate.intelligence.fragility_analyzer import FragilityAnalyzer, FragilityReport

class TestFragilityAnalyzer(unittest.TestCase):

    def test_robust_block(self):
        # 40x40x40 solid cube
        cube = trimesh.creation.box(extents=[40, 40, 40])
        report = FragilityAnalyzer.analyze(cube, num_slices=20, critical_diameter_mm=2.5)

        self.assertIsInstance(report, FragilityReport)
        self.assertEqual(report.total_fragile_features, 0)
        self.assertFalse(report.has_critical_necking)
        self.assertFalse(report.has_fragile_protrusions)
        self.assertEqual(report.fragility_risk_score, 0.0)

    def test_thin_protrusion(self):
        # Base cube (30x30x10) + Very thin vertical rod (diam 1.5mm, height 25mm)
        base = trimesh.creation.box(extents=[30, 30, 10])
        base.apply_translation([0, 0, 5])

        rod = trimesh.creation.cylinder(radius=0.75, height=25, sections=16) # Diam 1.5mm
        rod.apply_translation([0, 0, 22.5]) # Extends from Z=10 to Z=35

        mesh = base + rod
        report = FragilityAnalyzer.analyze(mesh, num_slices=30, critical_diameter_mm=2.5)

        self.assertTrue(report.has_fragile_protrusions)
        self.assertGreater(report.total_fragile_features, 0)
        self.assertGreaterEqual(report.fragility_risk_score, 4.0)
        self.assertTrue(any("Thin Protrusion Warning" in w for w in report.warnings))

    def test_structural_necking_hourglass(self):
        # Two large boxes (30x30x20) connected by a narrow waist (2x2x5)
        b_bottom = trimesh.creation.box(extents=[30, 30, 20])
        b_bottom.apply_translation([0, 0, 10])

        b_waist = trimesh.creation.box(extents=[2, 2, 6])
        b_waist.apply_translation([0, 0, 23])

        b_top = trimesh.creation.box(extents=[30, 30, 20])
        b_top.apply_translation([0, 0, 36])

        hourglass = b_bottom + b_waist + b_top
        report = FragilityAnalyzer.analyze(hourglass, num_slices=35)

        self.assertTrue(report.has_critical_necking)
        self.assertTrue(any("Structural Necking" in w for w in report.warnings))

if __name__ == "__main__":
    unittest.main()

