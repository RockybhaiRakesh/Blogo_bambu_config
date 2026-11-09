"""
Unit tests for PrintMate island detector.
"""

import unittest
import numpy as np
import trimesh

from printmate.geometry.island_detector import IslandDetector, IslandReport

class TestIslandDetector(unittest.TestCase):

    def test_single_solid_cube(self):
        cube = trimesh.creation.box(extents=[10, 10, 10])
        # Position base on Z=0
        cube.apply_translation([0, 0, 5.0])
        report = IslandDetector.analyze(cube, bed_clearance_mm=0.5)

        self.assertIsInstance(report, IslandReport)
        self.assertEqual(report.disconnected_components_count, 1)
        self.assertFalse(report.has_disconnected_debris)
        self.assertEqual(report.unsupported_minima_count, 0)

    def test_disconnected_bodies(self):
        b1 = trimesh.creation.box(extents=[10, 10, 10])
        b2 = trimesh.creation.box(extents=[4, 4, 4])
        b2.apply_translation([25.0, 0.0, 0.0])
        multi = b1 + b2

        report = IslandDetector.analyze(multi)
        self.assertEqual(report.disconnected_components_count, 2)
        self.assertEqual(len(report.component_volumes_cm3), 2)
        self.assertTrue(any("Multi-Body Mesh" in w for w in report.warnings))

    def test_floating_feature_minima(self):
        # Base cube on ground (Z from 0 to 10)
        base = trimesh.creation.box(extents=[20, 20, 10])
        base.apply_translation([0, 0, 5])

        # Overhanging arm in mid-air (Z from 15 to 20, extending from X=0 to 30)
        arm = trimesh.creation.box(extents=[10, 10, 5])
        arm.apply_translation([20, 0, 17.5])

        # Combined object
        arch = base + arm
        report = IslandDetector.analyze(arch, bed_clearance_mm=0.5)

        # The bottom of arm is at Z=15mm, which is a local minimum mid-air
        self.assertGreater(report.unsupported_minima_count, 0)
        self.assertTrue(any("Mid-Air Floating Islands" in w for w in report.warnings))

if __name__ == "__main__":
    unittest.main()

