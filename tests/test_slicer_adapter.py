"""
Unit tests for Slicer Adapter and Capability Probing (SlicerAdapter).
"""

import os
import unittest
from printmate.core.config import Config
from printmate.slicer.slicer_adapter import SlicerAdapter, SlicerCapability
from printmate.slicer.slicer_status import SlicerStatus, SlicerExecutionRecord

class TestSlicerAdapter(unittest.TestCase):

    def test_probe_bambu_studio_installation(self):
        """Verifies detection and native PE version probing of installed Bambu Studio."""
        caps = SlicerAdapter.probe_capabilities()
        self.assertIsInstance(caps, SlicerCapability)
        self.assertEqual(caps.slicer_name, "Bambu Studio")
        if os.path.exists(Config.BAMBU_STUDIO_EXE):
            self.assertTrue(caps.is_installed)
            self.assertIsNotNone(caps.version)
            self.assertTrue(caps.version.startswith("2.8"))
            self.assertTrue(caps.gui_available)
            # Strictly factual: official Windows build does not expose headless --slice CLI
            self.assertFalse(caps.supports_headless_slice)
            self.assertIn("--load_settings", caps.supported_cli_flags)

    def test_probe_nonexistent_executable(self):
        """Verifies clean capability reporting when executable is missing."""
        caps = SlicerAdapter.probe_capabilities(custom_exe="C:\\ghost\\slicer.exe")
        self.assertFalse(caps.is_installed)
        self.assertIsNone(caps.version)
        self.assertFalse(caps.supports_headless_slice)
        self.assertFalse(caps.gui_available)

    def test_execute_slice_nonexistent_project(self):
        """Verifies clean failure when target .3mf file is missing."""
        rec = SlicerAdapter.execute_slice(
            project_3mf="ghost_model.3mf",
            auto_launch_gui=False
        )
        self.assertIsInstance(rec, SlicerExecutionRecord)
        self.assertEqual(rec.status, SlicerStatus.PROJECT_VALIDATION_FAILED)
        self.assertGreater(len(rec.errors), 0)
        self.assertFalse(rec.physical_print_confirmed)

    def test_execute_slice_with_real_project(self):
        """Verifies slicer execution record for valid existing 3MF project."""
        p = "outputs/projects_3mf/Ready_single_color_single_55mm.3mf"
        if os.path.exists(p):
            rec = SlicerAdapter.execute_slice(
                project_3mf=p,
                printer_profile="Bambu Lab A1",
                filament_profile="pla_basic",
                auto_launch_gui=False
            )
            self.assertIn(rec.status, [SlicerStatus.SLICE_VALIDATED, SlicerStatus.SLICING_REQUIRED])
            self.assertEqual(rec.printer_profile, "Bambu Lab A1")
            # Must NEVER claim physical print confirmed
            self.assertFalse(rec.physical_print_confirmed)

    def test_execute_slice_split_project_requires_slicing(self):
        """Verifies that a split project without existing exported G-code returns SLICING_REQUIRED."""
        split_3mf = "outputs/projects_3mf/Ayyappan_Male_Female_Locked.3mf"
        if os.path.exists(split_3mf):
            rec = SlicerAdapter.execute_slice(
                project_3mf=split_3mf,
                printer_profile="Bambu Lab A1",
                filament_profile="pla_basic",
                auto_launch_gui=False
            )
            # Must NOT claim SLICE_VALIDATED using single_color G-code!
            self.assertEqual(rec.status, SlicerStatus.SLICING_REQUIRED)
            self.assertIsNone(rec.gcode_path)
            self.assertFalse(rec.is_gcode_validated)
            self.assertFalse(rec.physical_print_confirmed)

if __name__ == "__main__":
    unittest.main()

