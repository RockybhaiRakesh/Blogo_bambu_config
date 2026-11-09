"""
Unit tests for Calibration Test Generator (CalibrationGenerator).
"""

import os
import shutil
import tempfile
import unittest

from printmate.connectors.calibration_generator import CalibrationGenerator, CalibrationTestArtifacts
from printmate.connectors.connector_generator import ConnectorType

class TestCalibrationGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_calibration_coupons(self):
        """Verifies generation of physical calibration strips and worksheet."""
        res = CalibrationGenerator.generate_calibration_coupons(
            output_dir=self.temp_dir,
            connector_type=ConnectorType.D_SHAPED,
            clearances=[0.18, 0.22, 0.26],
            material="pla_basic"
        )
        self.assertIsInstance(res, CalibrationTestArtifacts)
        self.assertTrue(os.path.exists(res.male_coupon_path))
        self.assertTrue(os.path.exists(res.female_coupon_path))
        self.assertTrue(os.path.exists(res.project_3mf_path))
        self.assertTrue(os.path.exists(res.worksheet_md_path))
        self.assertEqual(res.clearances_tested, [0.18, 0.22, 0.26])

        # Verify worksheet content
        with open(res.worksheet_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Bambu Lab A1", content)
            self.assertIn("0.18 mm", content)
            self.assertIn("0.26 mm", content)

if __name__ == "__main__":
    unittest.main()

