"""
Unit tests for PrintMate orientation optimizer.
"""

import unittest
import numpy as np
import trimesh

from printmate.optimization.orientation_optimizer import OrientationOptimizer, OrientationReport

class TestOrientationOptimizer(unittest.TestCase):

    def test_flat_slab_ranking(self):
        # 60mm x 60mm x 10mm slab
        slab = trimesh.creation.box(extents=[60.0, 60.0, 10.0])
        report = OrientationOptimizer.optimize(slab, max_candidates=3)

        self.assertIsInstance(report, OrientationReport)
        self.assertEqual(len(report.top_candidates), 3)

        # The best orientation should be laying flat with largest bed contact
        best = report.recommended_orientation
        self.assertIsNotNone(best)
        self.assertGreater(best.bed_contact_area_cm2, 20.0) # 60x60 = 36cm2
        self.assertAlmostEqual(best.height_mm, 10.0, delta=1.0)
        self.assertTrue(best.fits_build_volume)

    def test_oversized_disqualification(self):
        # 300mm tall box (exceeds Bambu A1 256mm Z limit)
        tall_box = trimesh.creation.box(extents=[20.0, 20.0, 300.0])
        report = OrientationOptimizer.optimize(tall_box, max_candidates=3)

        # Default upright orientation should be flagged as not fitting build volume
        # Or an orientation laying it flat (if 300mm fits along X or Y? Wait, X and Y limit are also 256mm!)
        # Since 300mm exceeds all dimensions (256x256x256), no rotation fits
        for c in report.top_candidates:
            self.assertFalse(c.fits_build_volume)
            self.assertIn("Exceeds Bambu A1 build volume", c.explanation)

    def test_matrix_structure(self):
        cube = trimesh.creation.box(extents=[20, 20, 20])
        report = OrientationOptimizer.optimize(cube, max_candidates=3)

        for c in report.top_candidates:
            mat = np.array(c.rotation_matrix)
            self.assertEqual(mat.shape, (4, 4))
            # Homogeneous matrix last row is [0, 0, 0, 1]
            np.testing.assert_allclose(mat[3, :], [0, 0, 0, 1], atol=1e-4)

if __name__ == "__main__":
    unittest.main()

