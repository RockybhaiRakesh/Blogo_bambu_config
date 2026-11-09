"""
Unit tests for PrintMate model splitting and connector generation.
"""

import unittest
import numpy as np
import trimesh

from printmate.splitting.planar_splitter import PlanarSplitter
from printmate.splitting.split_analyzer import SplitAnalyzer
from printmate.connectors.connector_generator import ConnectorGenerator, DowelLockConfig
from printmate.core.exceptions import SplitError

class TestSplittingSubsystem(unittest.TestCase):

    def setUp(self):
        # Create a tall 20x20x60mm box centered at origin (Z from -30 to +30)
        self.tall_box = trimesh.creation.box(extents=[20.0, 20.0, 60.0])

    def test_planar_split(self):
        part_below, part_above = PlanarSplitter.split(
            mesh=self.tall_box,
            plane_normal=(0.0, 0.0, 1.0),
            plane_origin=(0.0, 0.0, 0.0),
            cap=True
        )

        self.assertIsInstance(part_below, trimesh.Trimesh)
        self.assertIsInstance(part_above, trimesh.Trimesh)
        self.assertGreater(len(part_below.faces), 0)
        self.assertGreater(len(part_above.faces), 0)
        self.assertTrue(part_below.is_watertight)
        self.assertTrue(part_above.is_watertight)

        # Check heights: each should be ~30mm
        self.assertAlmostEqual(part_below.extents[2], 30.0, places=1)
        self.assertAlmostEqual(part_above.extents[2], 30.0, places=1)

    def test_planar_split_out_of_bounds(self):
        # Slicing completely outside the mesh should raise SplitError
        with self.assertRaises(SplitError):
            PlanarSplitter.split(
                mesh=self.tall_box,
                plane_normal=(0.0, 0.0, 1.0),
                plane_origin=(0.0, 0.0, 200.0),
                cap=True
            )

    def test_split_analyzer_sampling(self):
        samples = SplitAnalyzer.sample_cross_sections(self.tall_box, axis=2, num_samples=10)
        self.assertGreater(len(samples), 0)
        # Perimeter of 20x20 square is 80mm
        for s in samples:
            self.assertAlmostEqual(s["length"], 80.0, delta=2.0)

    def test_connector_generator_geometry(self):
        cfg = DowelLockConfig(pin_radius=3.0, pin_height=5.0, clearance=0.25)
        pin = ConnectorGenerator.create_pin_mesh(cfg, origin=(0.0, 0.0, 0.0))
        cutter = ConnectorGenerator.create_socket_cutter_mesh(cfg, origin=(0.0, 0.0, 0.0))

        self.assertIsInstance(pin, trimesh.Trimesh)
        self.assertIsInstance(cutter, trimesh.Trimesh)
        self.assertTrue(pin.is_watertight)
        self.assertTrue(cutter.is_watertight)

        # Pin radius should be 3.0 (diameter ~6.0)
        self.assertAlmostEqual(pin.extents[0], 6.0, places=1)
        self.assertAlmostEqual(pin.extents[2], 5.0, places=1)

        # Cutter radius should be 3.25 (diameter ~6.5) and height 5.5
        self.assertAlmostEqual(cutter.extents[0], 6.5, places=1)
        self.assertAlmostEqual(cutter.extents[2], 5.5, places=1)

if __name__ == "__main__":
    unittest.main()

