"""
Unit tests for PrintMate geometry processing subsystem.
"""

import os
import unittest
import tempfile
import trimesh

from printmate.geometry.loader import load_mesh
from printmate.geometry.dimensions import calculate_dimensions, check_build_volume_fit
from printmate.geometry.mesh_validator import validate_mesh
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.core.exceptions import GeometryLoadError

class TestGeometrySubsystem(unittest.TestCase):

    def setUp(self):
        # Create a synthetic 20mm x 30mm x 40mm box
        self.box = trimesh.creation.box(extents=[20.0, 30.0, 40.0])
        self.temp_dir = tempfile.mkdtemp(prefix="test_geom_")
        self.test_stl = os.path.join(self.temp_dir, "box_test.stl")
        self.box.export(self.test_stl)

    def tearDown(self):
        if os.path.exists(self.test_stl):
            os.remove(self.test_stl)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_mesh_loading(self):
        loaded = load_mesh(self.test_stl)
        self.assertIsInstance(loaded, trimesh.Trimesh)
        self.assertEqual(len(loaded.vertices), len(self.box.vertices))
        self.assertEqual(len(loaded.faces), len(self.box.faces))

    def test_invalid_file_loading(self):
        with self.assertRaises(GeometryLoadError):
            load_mesh(os.path.join(self.temp_dir, "non_existent.stl"))

    def test_dimension_calculation(self):
        dims = calculate_dimensions(self.box)
        self.assertAlmostEqual(dims["dim_x"], 20.0, places=1)
        self.assertAlmostEqual(dims["dim_y"], 30.0, places=1)
        self.assertAlmostEqual(dims["dim_z"], 40.0, places=1)

    def test_build_volume_fit(self):
        fits, msg = check_build_volume_fit(20.0, 30.0, 40.0)
        self.assertTrue(fits)
        fits_over, msg_over = check_build_volume_fit(300.0, 100.0, 100.0)
        self.assertFalse(fits_over)

    def test_mesh_validation(self):
        validation = validate_mesh(self.box)
        self.assertTrue(validation["is_watertight"])
        self.assertEqual(validation["naked_edges_count"], 0)
        self.assertGreater(validation["volume_cm3"], 0)

    def test_geometry_analyzer(self):
        info = GeometryAnalyzer.analyze(self.test_stl)
        self.assertEqual(info.filename, "box_test.stl")
        self.assertAlmostEqual(info.dim_x, 20.0, places=1)
        self.assertAlmostEqual(info.dim_y, 30.0, places=1)
        self.assertAlmostEqual(info.dim_z, 40.0, places=1)
        self.assertTrue(info.is_watertight)

if __name__ == "__main__":
    unittest.main()
