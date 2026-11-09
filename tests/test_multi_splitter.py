"""
Unit tests for Intelligent Multi-Part Splitting module (MultiSplitter).
"""

import unittest
import trimesh

from printmate.splitting.multi_splitter import MultiSplitter, MultiSplitResult

class TestMultiSplitter(unittest.TestCase):

    def test_build_volume_check(self):
        """Verifies detection of models exceeding Bambu Lab A1 build limits."""
        small_box = trimesh.creation.box(extents=(100, 100, 100))
        exceeds, reasons = MultiSplitter.check_exceeds_volume(small_box)
        self.assertFalse(exceeds)
        self.assertEqual(len(reasons), 0)

        tall_box = trimesh.creation.box(extents=(50, 50, 300))
        exceeds_tall, reasons_tall = MultiSplitter.check_exceeds_volume(tall_box)
        self.assertTrue(exceeds_tall)
        self.assertEqual(len(reasons_tall), 1)
        self.assertIn("Z (Height)", reasons_tall[0])

    def test_multi_part_splitting_on_tall_model(self):
        """Tests sequential planar bisection on a 500mm tall cylinder."""
        cylinder = trimesh.creation.cylinder(radius=15.0, height=500.0)
        res = MultiSplitter.plan_and_execute(cylinder)

        self.assertIsInstance(res, MultiSplitResult)
        self.assertTrue(res.is_split_required)
        self.assertTrue(res.success)
        # 500mm requires at least 2 cuts -> 3 parts
        self.assertGreaterEqual(len(res.parts), 3)

        for p in res.parts:
            self.assertTrue(p.is_watertight)
            self.assertTrue(p.fits_build_plate)
            self.assertLessEqual(p.dimensions[2], 256.0)

    def test_avoid_fragile_zones(self):
        """Verifies that cut planes avoid specified fragile zones."""
        cylinder = trimesh.creation.cylinder(radius=15.0, height=500.0)
        # Fragile zone placed around target midpoint (Z = 0)
        fragile_zone = [{"z_min": -20.0, "z_max": 20.0, "name": "Mudra_Hands"}]

        cuts = MultiSplitter.find_safe_cut_planes(
            mesh=cylinder,
            axis=2,
            build_limit=256.0,
            fragile_zones=fragile_zone
        )
        for c in cuts:
            self.assertFalse(
                -20.0 <= c <= 20.0,
                f"Cut plane {c} violated fragile zone [-20, 20]"
            )

if __name__ == "__main__":
    unittest.main()

