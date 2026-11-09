"""
Unit tests for Intelligent Polygon Optimization module (MeshOptimizer).
"""

import os
import tempfile
import unittest
import numpy as np
import trimesh

from printmate.optimization.mesh_optimizer import MeshOptimizer, QualityLevel, OptimizationMetrics

class TestMeshOptimizer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a test high-density icosphere (~2,560 faces)
        self.sphere = trimesh.creation.icosphere(subdivisions=4, radius=15.0)
        self.sphere_path = os.path.join(self.temp_dir, "test_sphere.stl")
        self.sphere.export(self.sphere_path)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_high_poly(self):
        """Verifies threshold detection for high-polygon models."""
        self.assertFalse(MeshOptimizer.is_high_poly(self.sphere))
        # Large mock mesh
        self.assertTrue(MeshOptimizer.HIGH_POLY_THRESHOLD == 1_000_000)

    def test_adaptive_ratio_calculation(self):
        """Verifies adaptive decimation ratios for different quality levels."""
        # 2,000,000 faces
        r_balanced = MeshOptimizer.calculate_adaptive_ratio(2_000_000, QualityLevel.BALANCED)
        self.assertGreater(r_balanced, 0.05)
        self.assertLess(r_balanced, 0.30)

        r_preserve = MeshOptimizer.calculate_adaptive_ratio(2_000_000, QualityLevel.PRESERVE_DETAIL)
        self.assertGreater(r_preserve, r_balanced)

        r_aggressive = MeshOptimizer.calculate_adaptive_ratio(2_000_000, QualityLevel.AGGRESSIVE)
        self.assertLess(r_aggressive, r_balanced)

    def test_surface_deviation_measurement(self):
        """Verifies orthogonal surface deviation calculation."""
        sphere_b = self.sphere.copy()
        dev_exact = MeshOptimizer.measure_surface_deviation(self.sphere, sphere_b, sample_count=200)
        self.assertAlmostEqual(dev_exact, 0.0, places=3)

        # Perturbed sphere
        sphere_perturbed = trimesh.creation.icosphere(subdivisions=4, radius=15.2)
        dev_perturbed = MeshOptimizer.measure_surface_deviation(self.sphere, sphere_perturbed, sample_count=200)
        self.assertGreater(dev_perturbed, 0.15)
        self.assertLess(dev_perturbed, 0.25)

    def test_optimize_and_quality_gates(self):
        """Tests end-to-end decimation and quality gate acceptance."""
        out_path = os.path.join(self.temp_dir, "opt_sphere.stl")
        metrics = MeshOptimizer.optimize(
            input_path=self.sphere_path,
            output_path=out_path,
            quality=QualityLevel.AGGRESSIVE
        )
        self.assertIsInstance(metrics, OptimizationMetrics)
        self.assertTrue(metrics.is_accepted)
        self.assertGreater(metrics.reduction_pct, 40.0)
        self.assertLess(metrics.volume_deviation_pct, 2.0)
        self.assertTrue(metrics.is_watertight)
        self.assertTrue(os.path.exists(out_path))

    def test_quality_gate_rejection_on_strict_bounds(self):
        """Verifies rejection when quality threshold is breached."""
        out_path = os.path.join(self.temp_dir, "opt_rejected.stl")
        # Set impossible max_bounds_delta limit
        metrics = MeshOptimizer.optimize(
            input_path=self.sphere_path,
            output_path=out_path,
            quality=QualityLevel.AGGRESSIVE,
            max_bounds_delta_mm=0.000001
        )
        self.assertFalse(metrics.is_accepted)
        self.assertIsNotNone(metrics.rejection_reason)
        # Verify bad output file is purged
        self.assertFalse(os.path.exists(out_path))

if __name__ == "__main__":
    unittest.main()

