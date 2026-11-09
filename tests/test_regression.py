"""
Regression test suite for PrintMate AI.
Ensures backward compatibility with original print_pilot.py CLI, function signatures,
and parameter preservation across all subsystems.
"""

import os
import sys
import subprocess
import unittest
import tempfile
import trimesh

import print_pilot
from printmate.core.config import Config
from printmate.geometry.analyzer import GeometryAnalyzer
from printmate.slicer.project_generator import BambuProjectGenerator
from printmate.slicer.slicer_validator import SlicerValidator

class TestPrintMateRegression(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_reg_")
        self.box_stl = os.path.join(self.temp_dir, "regression_box.stl")
        # 15 x 25 x 50 mm box (miniature scale <65mm)
        mesh = trimesh.creation.box(extents=[15.0, 25.0, 50.0])
        mesh.export(self.box_stl)

    def tearDown(self):
        if os.path.exists(self.box_stl):
            os.remove(self.box_stl)
        for f in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    def test_legacy_analyze_model_function(self):
        """Verifies that print_pilot.analyze_model() returns identical schema."""
        info = print_pilot.analyze_model(self.box_stl)
        self.assertIn("file", info)
        self.assertIn("filename", info)
        self.assertIn("dim_x", info)
        self.assertIn("dim_y", info)
        self.assertIn("dim_z", info)
        self.assertIn("faces", info)
        self.assertIn("vertices", info)
        self.assertIn("is_watertight", info)
        self.assertIn("volume_cm3", info)

        self.assertAlmostEqual(info["dim_x"], 15.0, places=1)
        self.assertAlmostEqual(info["dim_y"], 25.0, places=1)
        self.assertAlmostEqual(info["dim_z"], 50.0, places=1)
        self.assertTrue(info["is_watertight"])

    def test_legacy_create_safe_bambu_project_function(self):
        """Verifies print_pilot.create_safe_bambu_project() generates valid 3MF."""
        if not os.path.exists(Config.GOLDEN_TEMPLATE_3MF):
            self.skipTest("Golden template 3MF not present.")

        out_3mf = os.path.join(self.temp_dir, "reg_out.3mf")
        result = print_pilot.create_safe_bambu_project(
            input_file=self.box_stl,
            output_3mf=out_3mf,
            mode="single",
            filament="pla_basic",
            target_height=50.0
        )
        self.assertTrue(os.path.exists(result))
        is_valid, errs = SlicerValidator.validate_package(result)
        self.assertTrue(is_valid, f"Regression 3MF validation failed: {errs}")

    def test_cli_help_invocation(self):
        """Verifies python print_pilot.py --help succeeds with code 0."""
        cmd = [sys.executable, "print_pilot.py", "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=Config.WORKSPACE_DIR)
        self.assertEqual(res.returncode, 0)
        self.assertIn("--model", res.stdout)
        self.assertIn("--mode", res.stdout)
        self.assertIn("--filament", res.stdout)
        self.assertIn("--height", res.stdout)
        self.assertIn("--launch", res.stdout)

    def test_cli_execution_headless(self):
        """Verifies python print_pilot.py runs pipeline end-to-end without --launch."""
        if not os.path.exists(Config.GOLDEN_TEMPLATE_3MF):
            self.skipTest("Golden template 3MF not present.")

        cmd = [
            sys.executable,
            "print_pilot.py",
            "--model", self.box_stl,
            "--mode", "single",
            "--filament", "pla_basic",
            "--height", "50.0"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=Config.WORKSPACE_DIR)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        self.assertIn("Scanning model:", res.stdout)
        self.assertIn("Generating Bambu Studio Project:", res.stdout)
        self.assertIn("Project generated successfully at:", res.stdout)

        # Check that expected 3MF was created
        expected_3mf = os.path.join(Config.WORKSPACE_DIR, "Ready_regression_box_single_50mm.3mf")
        self.assertTrue(os.path.exists(expected_3mf))
        if os.path.exists(expected_3mf):
            os.remove(expected_3mf)

if __name__ == "__main__":
    unittest.main()

