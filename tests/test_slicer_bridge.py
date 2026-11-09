"""
Unit tests for PrintMate Bambu Studio slicer bridge and G-code parser.
"""

import os
import unittest
import tempfile

from printmate.core.config import Config
from printmate.slicer.slicer_bridge import SlicerBridge, SlicingResult
from printmate.core.exceptions import SlicerIntegrationError

class TestSlicerBridge(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_slicer_")
        self.sample_gcode = os.path.join(self.temp_dir, "sample.gcode")

        # Create a synthetic Bambu-compliant G-code header
        gcode_content = """
; model printing time: 1h 30m 00s; total estimated time: 1h 45m 12s
; total layer number: 450
; total filament length [mm] : 1850.50
; total filament weight [g] : 5.62
; default_filament_profile = "Bambu PLA Basic @BBL A1"
G28 ; Home
M104 S220 ; Set extruder temp
M140 S60 ; Set bed temp
G1 Z0.2 F1200
"""
        with open(self.sample_gcode, "w", encoding="utf-8") as f:
            f.write(gcode_content.strip())

    def tearDown(self):
        if os.path.exists(self.sample_gcode):
            os.remove(self.sample_gcode)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_probe_capabilities(self):
        caps = SlicerBridge.probe_capabilities()
        self.assertIn("executable", caps)
        self.assertIn("exists", caps)
        self.assertIn("supports_headless_slice", caps)
        self.assertIn("known_flags", caps)

    def test_parse_synthetic_gcode(self):
        meta = SlicerBridge.parse_gcode(self.sample_gcode)
        self.assertEqual(meta["estimated_time"], "1h 45m 12s")
        self.assertEqual(meta["total_layers"], 450)
        self.assertAlmostEqual(meta["filament_weight_g"], 5.62, places=2)
        self.assertAlmostEqual(meta["filament_length_mm"], 1850.50, places=1)
        self.assertEqual(meta["filament_profile"], "Bambu PLA Basic @BBL A1")

    def test_parse_real_project_gcode(self):
        real_gcode = os.path.join(Config.WORKSPACE_DIR, "outputs", "gcode", "single_color_PLA_2h20m.gcode")
        if not os.path.exists(real_gcode):
            real_gcode = os.path.join(Config.WORKSPACE_DIR, "single_color_PLA_2h20m.gcode")

        if os.path.exists(real_gcode):
            meta = SlicerBridge.parse_gcode(real_gcode)
            self.assertIsNotNone(meta["estimated_time"])
            self.assertIsNotNone(meta["total_layers"])
            self.assertIsNotNone(meta["filament_weight_g"])
            self.assertGreater(meta["total_layers"], 100)

    def test_parse_nonexistent_gcode(self):
        with self.assertRaises(SlicerIntegrationError):
            SlicerBridge.parse_gcode(os.path.join(self.temp_dir, "ghost.gcode"))

    def test_execute_slicing_result(self):
        # Test on dummy non-existent 3MF
        res = SlicerBridge.execute_slicing("non_existent_project.3mf")
        self.assertIsInstance(res, SlicingResult)
        self.assertFalse(res.success)
        self.assertIn("not found", res.message)

if __name__ == "__main__":
    unittest.main()

