"""
Unit tests for PrintMate 3MF packaging and Bambu Studio configuration injection.
"""

import os
import json
import zipfile
import unittest
import tempfile
import trimesh

from printmate.core.config import Config
from printmate.slicer.slicer_validator import SlicerValidator
from printmate.slicer.project_generator import BambuProjectGenerator
from printmate.optimization.strategy_optimizer import StrategyOptimizer

class Test3MFSubsystem(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_3mf_")
        self.synthetic_stl = os.path.join(self.temp_dir, "test_cube.stl")
        cube = trimesh.creation.box(extents=[10, 10, 10])
        cube.export(self.synthetic_stl)

    def tearDown(self):
        if os.path.exists(self.synthetic_stl):
            os.remove(self.synthetic_stl)
        # Clean any generated 3mf files
        for f in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    def test_slicer_validator_nonexistent_file(self):
        valid, errs = SlicerValidator.validate_package(os.path.join(self.temp_dir, "ghost.3mf"))
        self.assertFalse(valid)
        self.assertGreater(len(errs), 0)

    def test_slicer_validator_invalid_archive(self):
        fake_file = os.path.join(self.temp_dir, "fake.3mf")
        with open(fake_file, "w") as f:
            f.write("not a zip archive")
        valid, errs = SlicerValidator.validate_package(fake_file)
        self.assertFalse(valid)
        self.assertIn("not a valid zip", errs[0])

    def test_strategy_optimizer_single_mode(self):
        cfg = StrategyOptimizer.build_slicer_overrides(mode="single", filament="pla_basic")
        self.assertEqual(cfg["layer_height"], "0.12")
        self.assertEqual(cfg["wall_loops"], "3")
        self.assertEqual(cfg["sparse_infill_pattern"], "gyroid")
        self.assertEqual(cfg["enable_support"], "1")
        self.assertEqual(cfg["support_top_z_distance"], "0.24")
        self.assertEqual(cfg["support_object_xy_distance"], "0.60")

    def test_strategy_optimizer_silk_filament(self):
        cfg = StrategyOptimizer.build_slicer_overrides(mode="single", filament="pla_silk")
        self.assertEqual(cfg["support_top_z_distance"], "0.26")
        self.assertEqual(cfg["outer_wall_speed"], ["45"])

    def test_project_generator_build_and_validate(self):
        # Only run if golden template exists
        if not os.path.exists(Config.GOLDEN_TEMPLATE_3MF):
            self.skipTest(f"Golden template not found at {Config.GOLDEN_TEMPLATE_3MF}")

        out_3mf = os.path.join(self.temp_dir, "output_project.3mf")
        gen_path = BambuProjectGenerator.generate(
            input_file=self.synthetic_stl,
            output_3mf=out_3mf,
            mode="single",
            filament="pla_basic",
            target_height=55.0
        )

        self.assertTrue(os.path.exists(gen_path))

        # Validate package
        is_valid, errs = SlicerValidator.validate_package(gen_path)
        self.assertTrue(is_valid, f"Validation errors: {errs}")

        # Unpack and verify injected JSON settings
        with zipfile.ZipFile(gen_path, 'r') as zf:
            cfg_bytes = zf.read("Metadata/project_settings.config")
            cfg = json.loads(cfg_bytes.decode('utf-8'))
            self.assertEqual(cfg["layer_height"], "0.12")
            self.assertEqual(cfg["support_top_z_distance"], "0.24")
            self.assertEqual(cfg["wall_loops"], "3")
            self.assertEqual(cfg["sparse_infill_pattern"], "gyroid")

if __name__ == "__main__":
    unittest.main()

