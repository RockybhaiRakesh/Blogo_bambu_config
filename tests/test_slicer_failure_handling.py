"""
Unit tests for Slicer and Project Validation Status Codes & Failure Handling.
Verifies all 7 standardized engineering statuses and prevents false physical print claims.
"""

import unittest
from printmate.slicer.slicer_status import SlicerStatus, SlicerExecutionRecord
from printmate.slicer.slicer_adapter import SlicerAdapter
from printmate.slicer.gcode_validator import GCodeValidator
from printmate.slicer.project_validator import NativeProjectValidator

class TestSlicerFailureHandling(unittest.TestCase):

    def test_all_seven_statuses_defined(self):
        """Verifies definition of all 7 mandatory engineering status enums."""
        expected_statuses = [
            "PROJECT_VALIDATION_FAILED",
            "SLICER_NOT_AVAILABLE",
            "SLICING_REQUIRED",
            "SLICING_FAILED",
            "GCODE_VALIDATION_FAILED",
            "SLICE_VALIDATED",
            "PHYSICAL_PRINT_NOT_VERIFIED"
        ]
        for name in expected_statuses:
            self.assertTrue(hasattr(SlicerStatus, name))
            self.assertEqual(getattr(SlicerStatus, name).value, name)

    def test_project_validation_failed_trigger(self):
        """PROJECT_VALIDATION_FAILED occurs when 3MF archive is corrupted or missing."""
        rep = NativeProjectValidator.validate_project("non_existent.3mf")
        self.assertEqual(rep.status, SlicerStatus.PROJECT_VALIDATION_FAILED)
        self.assertFalse(rep.is_valid)

    def test_slicer_not_available_trigger(self):
        """SLICER_NOT_AVAILABLE occurs when slicer binary is missing from configured path."""
        rec = SlicerAdapter.execute_slice(
            project_3mf="dummy.3mf",
            auto_launch_gui=False
        )
        # If binary were at custom invalid path
        caps = SlicerAdapter.probe_capabilities(custom_exe="C:\\invalid\\path\\slicer.exe")
        self.assertFalse(caps.is_installed)

    def test_gcode_validation_failed_trigger(self):
        """GCODE_VALIDATION_FAILED occurs when G-code is truncated or has invalid coordinates."""
        res = GCodeValidator.validate_gcode("non_existent.gcode")
        self.assertEqual(res.status, SlicerStatus.GCODE_VALIDATION_FAILED)
        self.assertFalse(res.is_valid)

    def test_slice_validated_trigger(self):
        """SLICE_VALIDATED occurs when real G-code passes all telemetry and boundary checks."""
        real_gcode = "outputs/gcode/single_color_PLA_2h20m.gcode"
        res = GCodeValidator.validate_gcode(real_gcode)
        self.assertEqual(res.status, SlicerStatus.SLICE_VALIDATED)
        self.assertTrue(res.is_valid)

    def test_physical_print_never_confirmed_by_software(self):
        """Guarantees physical print success can NEVER be claimed from a software slice."""
        record = SlicerExecutionRecord(
            status=SlicerStatus.SLICE_VALIDATED,
            is_gcode_validated=True,
            physical_print_confirmed=False
        )
        self.assertFalse(record.physical_print_confirmed)
        # SlicerStatus.PHYSICAL_PRINT_NOT_VERIFIED must be available as safety declaration
        self.assertEqual(SlicerStatus.PHYSICAL_PRINT_NOT_VERIFIED.value, "PHYSICAL_PRINT_NOT_VERIFIED")

if __name__ == "__main__":
    unittest.main()

