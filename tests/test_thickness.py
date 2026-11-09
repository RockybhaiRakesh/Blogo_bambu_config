"""
Unit tests for PrintMate wall thickness analyzer.
"""

import unittest
import numpy as np
import trimesh

from printmate.geometry.thickness_analyzer import ThicknessAnalyzer, ThicknessReport

class TestThicknessAnalyzer(unittest.TestCase):

    def test_thick_cube(self):
        # 10x10x10 mm solid cube
        cube = trimesh.creation.box(extents=[10.0, 10.0, 10.0])
        report = ThicknessAnalyzer.analyze(cube, sample_count=50)

        self.assertIsInstance(report, ThicknessReport)
        self.assertGreater(report.samples_evaluated, 0)
        # In a 10x10x10 cube, opposing wall distance from face center is 10.0mm
        self.assertAlmostEqual(report.min_thickness, 10.0, places=1)
        self.assertEqual(report.critical_samples_count, 0)
        self.assertEqual(report.caution_samples_count, 0)
        self.assertEqual(len(report.warnings), 0)

    def test_critical_thin_wall(self):
        # Thin box of thickness 0.3mm (below 0.4mm nozzle)
        thin_plate = trimesh.creation.box(extents=[20.0, 20.0, 0.3])
        report = ThicknessAnalyzer.analyze(thin_plate, sample_count=50, nozzle_diameter=0.4)

        self.assertAlmostEqual(report.min_thickness, 0.3, places=1)
        self.assertGreater(report.critical_samples_count, 0)
        self.assertTrue(any("Critical Thin Walls" in w for w in report.warnings))

    def test_sub_perimeter_thin_wall(self):
        # Box of thickness 0.6mm (between 0.4mm and 0.8mm)
        plate = trimesh.creation.box(extents=[20.0, 20.0, 0.6])
        report = ThicknessAnalyzer.analyze(plate, sample_count=50, nozzle_diameter=0.4)

        self.assertAlmostEqual(report.min_thickness, 0.6, places=1)
        self.assertEqual(report.critical_samples_count, 0)
        self.assertGreater(report.caution_samples_count, 0)
        self.assertTrue(any("Sub-Perimeter Thin Walls" in w for w in report.warnings))

if __name__ == "__main__":
    unittest.main()

