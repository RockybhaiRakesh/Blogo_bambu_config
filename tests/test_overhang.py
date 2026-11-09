"""
Unit tests for PrintMate overhang analyzer.
"""

import unittest
import numpy as np
import trimesh

from printmate.geometry.overhang_analyzer import OverhangAnalyzer, OverhangReport

class TestOverhangAnalyzer(unittest.TestCase):

    def test_upward_pyramid(self):
        # A pyramid tapering towards top (Z > 0) has all side faces sloping upward (nz > 0)
        # Base on ground, tip at Z=10
        vertices = np.array([
            [-5.0, -5.0, 0.0],
            [5.0, -5.0, 0.0],
            [5.0, 5.0, 0.0],
            [-5.0, 5.0, 0.0],
            [0.0, 0.0, 10.0]
        ])
        faces = np.array([
            [0, 2, 1], [0, 3, 2],  # Bottom base (facing down)
            [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4] # Sides sloping upward
        ])
        pyramid = trimesh.Trimesh(vertices=vertices, faces=faces)

        report = OverhangAnalyzer.analyze(pyramid, threshold_angle_deg=45.0)
        self.assertIsInstance(report, OverhangReport)
        self.assertGreater(report.total_surface_area_cm2, 0)
        # Only bottom face faces downward (horizontal 90°)
        self.assertAlmostEqual(report.horizontal_roof_area_cm2, 1.0, places=1) # 10x10mm = 100mm2 = 1.0cm2

    def test_inverted_pyramid(self):
        # Inverted pyramid where tip is at Z=0 and base is at Z=10
        vertices = np.array([
            [0.0, 0.0, 0.0],       # Tip at bottom
            [-10.0, -10.0, 10.0],
            [10.0, -10.0, 10.0],
            [10.0, 10.0, 10.0],
            [-10.0, 10.0, 10.0]
        ])
        faces = np.array([
            [1, 2, 3], [1, 3, 4],  # Top base (facing upward nz > 0)
            [0, 2, 1], [0, 3, 2], [0, 4, 3], [0, 1, 4] # Downward sloping sides
        ])
        inv_pyr = trimesh.Trimesh(vertices=vertices, faces=faces)

        report = OverhangAnalyzer.analyze(inv_pyr, threshold_angle_deg=30.0)
        # The 4 sides all face downward with slope
        self.assertGreater(report.total_overhang_area_cm2, 0.0)
        self.assertGreater(report.overhang_percentage, 20.0)

    def test_threshold_sensitivity(self):
        # Cube of 10x10x10
        cube = trimesh.creation.box(extents=[10, 10, 10])
        rep_strict = OverhangAnalyzer.analyze(cube, threshold_angle_deg=30.0)
        rep_lenient = OverhangAnalyzer.analyze(cube, threshold_angle_deg=89.0)

        # In a cube, vertical faces have 0° overhang from vertical.
        # Only bottom face has 90° overhang from vertical.
        self.assertAlmostEqual(rep_strict.total_overhang_area_cm2, 1.0, places=1)
        self.assertAlmostEqual(rep_lenient.total_overhang_area_cm2, 1.0, places=1)

if __name__ == "__main__":
    unittest.main()

