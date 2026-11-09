"""
Unit tests for Native Bambu Studio Project Validator module (NativeProjectValidator).
"""

import os
import unittest
from printmate.slicer.project_validator import NativeProjectValidator, ProjectValidationReport
from printmate.slicer.slicer_status import SlicerStatus

class TestNativeProjectValidator(unittest.TestCase):

    def test_validate_existing_golden_3mf(self):
        """Verifies validation of existing generated Bambu Studio 3MF archives."""
        p1 = "outputs/projects_3mf/Ready_single_color_single_55mm.3mf"
        p2 = "outputs/projects_3mf/Ayyappan_Male_Female_Locked.3mf"

        for p in [p1, p2]:
            if os.path.exists(p):
                rep = NativeProjectValidator.validate_project(p)
                self.assertIsInstance(rep, ProjectValidationReport)
                self.assertTrue(rep.is_valid)
                # Valid 3MF on disk must have status SLICING_REQUIRED (never SLICE_VALIDATED before G-code)
                self.assertEqual(rep.status, SlicerStatus.SLICING_REQUIRED)
                self.assertIn("Bambu Lab A1", rep.printer_model)
                self.assertEqual(rep.nozzle_diameter, "0.4")
                self.assertEqual(len(rep.errors), 0)

    def test_validate_split_project_components(self):
        """Verifies multi-object connector split project component counting and metadata."""
        split_3mf = "outputs/projects_3mf/Ayyappan_Male_Female_Locked.3mf"
        if not os.path.exists(split_3mf):
            self.skipTest(f"Split project {split_3mf} not found.")

        rep = NativeProjectValidator.validate_project(split_3mf)
        self.assertTrue(rep.is_valid)
        self.assertEqual(rep.status, SlicerStatus.SLICING_REQUIRED)
        self.assertEqual(rep.objects_count, 2)
        self.assertTrue(any("MaleLock" in name for name in rep.object_names))
        self.assertTrue(any("FemaleLock" in name for name in rep.object_names))
        self.assertTrue(rep.fits_build_plate)

    def test_validate_nonexistent_file(self):
        """Verifies clean failure when 3MF file does not exist."""
        rep = NativeProjectValidator.validate_project("non_existent_file.3mf")
        self.assertFalse(rep.is_valid)
        self.assertEqual(rep.status, SlicerStatus.PROJECT_VALIDATION_FAILED)
        self.assertGreater(len(rep.errors), 0)

if __name__ == "__main__":
    unittest.main()

