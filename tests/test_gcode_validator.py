"""
Unit tests for Deep G-code Telemetry and Coordinate Validation (GCodeValidator).
"""

import os
import unittest
import tempfile
from printmate.slicer.gcode_validator import GCodeValidator, GCodeValidationResult, GCodeMetadata
from printmate.slicer.slicer_status import SlicerStatus

class TestGCodeValidator(unittest.TestCase):

    REAL_GCODE = "outputs/gcode/single_color_PLA_2h20m.gcode"

    def test_validate_real_bambu_gcode(self):
        """Validates real Bambu Studio 02.08.02.61 G-code file telemetry."""
        if not os.path.exists(self.REAL_GCODE):
            self.skipTest(f"Real G-code file {self.REAL_GCODE} not present.")

        res = GCodeValidator.validate_gcode(self.REAL_GCODE, expected_printer="Bambu Lab A1")
        self.assertIsInstance(res, GCodeValidationResult)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, SlicerStatus.SLICE_VALIDATED)
        self.assertIsNotNone(res.metadata)

        meta = res.metadata
        self.assertIn("BambuStudio 02.08.02.61", meta.slicer_version)
        self.assertAlmostEqual(meta.total_filament_weight_g, 7.87, places=2)
        self.assertEqual(meta.total_layers, 741)
        self.assertAlmostEqual(meta.max_z_height_mm, 55.0, places=1)
        self.assertIn("2h 19m 31s", meta.total_estimated_time_str)
        self.assertAlmostEqual(meta.total_estimated_time_minutes, 139.5, delta=1.0)
        self.assertEqual(meta.bed_type, "Textured PEI Plate")
        self.assertTrue(meta.is_within_build_plate)

        # Distinguish actual telemetry from heuristic predictions
        self.assertTrue(meta.is_actual_slicer_output)
        self.assertFalse(meta.is_heuristic_estimate)

        # Coordinate Separation Verification: Model Extrusion vs Maintenance
        self.assertGreater(meta.model_min_x, 110.0)
        self.assertLess(meta.model_max_x, 150.0)
        self.assertGreater(meta.model_min_y, 110.0)
        self.assertLess(meta.model_max_y, 145.0)

        # First layer printed bounds must be positive and within bed (NOT -48.2mm!)
        self.assertGreater(meta.first_layer_min_x, 100.0)
        self.assertLess(meta.first_layer_max_x, 150.0)

        # Off-bed machine maintenance (wiper at -48.2mm, cutter at 267.0mm) recorded separately
        self.assertAlmostEqual(meta.maintenance_min_x, -48.2, places=1)
        self.assertAlmostEqual(meta.maintenance_max_x, 267.0, places=1)

    def test_negative_coordinate_model_extrusion_rejection(self):
        """Verifies rejection when actual model extrusion coordinates are negative or exceed bed."""
        sample_gcode = (
            "; HEADER_BLOCK_START\n"
            "; BambuStudio 02.08.02.61\n"
            "; total estimated time: 5m 0s\n"
            "; total filament weight [g] : 1.0\n"
            "; total layer number: 10\n"
            "; max_z_height: 5.00\n"
            "; HEADER_BLOCK_END\n"
            "; CONFIG_BLOCK_START\n"
            "; curr_bed_type = Textured PEI Plate\n"
            "; CONFIG_BLOCK_END\n"
            "; FEATURE: Outer wall\n"
            "G1 X-5.0 Y20.0 E1.5\n"   # Model extrusion outside bed (X < 0)
            "G1 X15.0 Y20.0 E3.0\n"   # Small 20mm span, but physically off-bed!
            "M73 P100 R0\n"
            "; EXECUTABLE_BLOCK_END\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as tf:
            tf.write(sample_gcode * 20)  # > 1KB
            neg_path = tf.name

        try:
            res = GCodeValidator.validate_gcode(neg_path, max_build_volume=(256.0, 256.0, 256.0))
            self.assertFalse(res.is_valid)
            self.assertEqual(res.status, SlicerStatus.GCODE_VALIDATION_FAILED)
            self.assertFalse(res.metadata.is_within_build_plate)
            self.assertTrue(any("exceed printable bed" in e.lower() for e in res.errors))
        finally:
            if os.path.exists(neg_path):
                os.remove(neg_path)

    def test_separated_purge_wipe_maintenance_vs_model(self):
        """Verifies off-bed wipe/purge moves do not fail bed fit when model extrusions are within bed."""
        sample_gcode = (
            "; HEADER_BLOCK_START\n"
            "; BambuStudio 02.08.02.61\n"
            "; total estimated time: 5m 0s\n"
            "; total filament weight [g] : 1.0\n"
            "; total layer number: 10\n"
            "; max_z_height: 5.00\n"
            "; HEADER_BLOCK_END\n"
            "; CONFIG_BLOCK_START\n"
            "; curr_bed_type = Textured PEI Plate\n"
            "; CONFIG_BLOCK_END\n"
            "G1 X-48.2 Y100.0\n"       # Off-bed nozzle wipe travel (no extrusion)
            "G1 X267.0 Y100.0\n"       # Off-bed filament cutter travel (no extrusion)
            "; FEATURE: Outer wall\n"
            "G1 X100.0 Y100.0 E1.0\n"   # Model extrusion cleanly on bed
            "G1 X120.0 Y120.0 E2.0\n"
            "M73 P100 R0\n"
            "; EXECUTABLE_BLOCK_END\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as tf:
            tf.write(sample_gcode * 20)
            wipe_path = tf.name

        try:
            res = GCodeValidator.validate_gcode(wipe_path, max_build_volume=(256.0, 256.0, 256.0))
            self.assertTrue(res.is_valid)
            self.assertEqual(res.status, SlicerStatus.SLICE_VALIDATED)
            self.assertTrue(res.metadata.is_within_build_plate)
            self.assertAlmostEqual(res.metadata.maintenance_min_x, -48.2, places=1)
            self.assertAlmostEqual(res.metadata.model_min_x, 100.0, places=1)
        finally:
            if os.path.exists(wipe_path):
                os.remove(wipe_path)

    def test_support_z_gap_layer_height_aware(self):
        """Verifies 0.16mm support top Z gap is accepted at 0.08mm layer height (2 full layers)."""
        sample_gcode = (
            "; HEADER_BLOCK_START\n"
            "; BambuStudio 02.08.02.61\n"
            "; total estimated time: 5m 0s\n"
            "; total filament weight [g] : 1.0\n"
            "; total layer number: 10\n"
            "; max_z_height: 5.00\n"
            "; HEADER_BLOCK_END\n"
            "; CONFIG_BLOCK_START\n"
            "; curr_bed_type = Textured PEI Plate\n"
            "; layer_height = 0.08\n"
            "; enable_support = 1\n"
            "; support_top_z_distance = 0.16\n"
            "; CONFIG_BLOCK_END\n"
            "; FEATURE: Outer wall\n"
            "G1 X100.0 Y100.0 E1.0\n"
            "M73 P100 R0\n"
            "; EXECUTABLE_BLOCK_END\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as tf:
            tf.write(sample_gcode * 20)
            gap_path = tf.name

        try:
            res = GCodeValidator.validate_gcode(gap_path, max_build_volume=(256.0, 256.0, 256.0))
            self.assertTrue(res.is_valid)
            self.assertEqual(len(res.warnings), 0)
            self.assertAlmostEqual(res.metadata.support_top_z_gap, 0.16, places=2)
        finally:
            if os.path.exists(gap_path):
                os.remove(gap_path)

    def test_missing_gcode_file(self):
        """Verifies clean failure and status when G-code is missing."""
        res = GCodeValidator.validate_gcode("ghost.gcode")
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, SlicerStatus.GCODE_VALIDATION_FAILED)
        self.assertGreater(len(res.errors), 0)

    def test_truncated_corrupt_gcode(self):
        """Verifies rejection of invalid or corrupt G-code files."""
        with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as tf:
            tf.write("; incomplete test file without headers\nG1 X10 Y10\n")
            corrupt_path = tf.name

        try:
            res = GCodeValidator.validate_gcode(corrupt_path)
            self.assertFalse(res.is_valid)
            self.assertEqual(res.status, SlicerStatus.GCODE_VALIDATION_FAILED)
            self.assertTrue(any("HEADER_BLOCK_START missing" in e or "truncated" in e for e in res.errors))
        finally:
            if os.path.exists(corrupt_path):
                os.remove(corrupt_path)

    def test_out_of_bounds_coordinate_detection(self):
        """Verifies detection of toolpaths that exceed physical build plate boundaries."""
        sample_gcode = (
            "; HEADER_BLOCK_START\n"
            "; BambuStudio 02.08.02.61\n"
            "; total estimated time: 10m 0s\n"
            "; total filament weight [g] : 5.0\n"
            "; total layer number: 50\n"
            "; max_z_height: 290.00\n"  # Exceeds 256mm A1 volume
            "; HEADER_BLOCK_END\n"
            "; CONFIG_BLOCK_START\n"
            "; curr_bed_type = Textured PEI Plate\n"
            "; CONFIG_BLOCK_END\n"
            "G1 X350 Y100 E5\n"         # Exceeds 256mm X bed
            "M73 P100 R0\n"
            "; EXECUTABLE_BLOCK_END\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as tf:
            tf.write(sample_gcode * 20)  # Make > 1KB
            bound_path = tf.name

        try:
            res = GCodeValidator.validate_gcode(bound_path, max_build_volume=(256.0, 256.0, 256.0))
            self.assertFalse(res.is_valid)
            self.assertEqual(res.status, SlicerStatus.GCODE_VALIDATION_FAILED)
            self.assertTrue(any("exceed" in e.lower() for e in res.errors))
        finally:
            if os.path.exists(bound_path):
                os.remove(bound_path)

if __name__ == "__main__":
    unittest.main()

