"""
Unit tests for Hardware and Material Compatibility Validator (SettingsValidator).
"""

import unittest
from printmate.optimization.settings_validator import SettingsValidator, CompatibilityResult
from printmate.profiles.printer_profiles import PrinterProfileRegistry, PrinterProfile
from printmate.profiles.filament_profiles import FilamentProfileRegistry

class TestSettingsValidator(unittest.TestCase):

    def setUp(self):
        self.a1 = PrinterProfileRegistry.get_profile("Bambu Lab A1")
        self.x1c = PrinterProfileRegistry.get_profile("Bambu Lab X1-Carbon")

    def test_compatible_pairing(self):
        """Bambu A1 + PLA Basic must be 100% compatible with 0 errors and 0 warnings."""
        pla = FilamentProfileRegistry.get_profile("pla_basic")
        res = SettingsValidator.validate_pairing(self.a1, pla)
        self.assertTrue(res.is_compatible)
        self.assertTrue(res.is_safe_to_slice)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(len(res.warnings), 0)

    def test_enclosure_missing_warning(self):
        """Bambu A1 (open bed) + ABS/PC must issue an ENCLOSURE MISSING warning."""
        abs_prof = FilamentProfileRegistry.get_profile("abs")
        res = SettingsValidator.validate_pairing(self.a1, abs_prof)
        self.assertTrue(res.is_compatible)  # Still technically sliceable, but warned
        self.assertGreater(len(res.warnings), 0)
        self.assertTrue(any("ENCLOSURE MISSING" in w for w in res.warnings))

    def test_abrasive_composite_warning(self):
        """Bambu A1 (standard nozzle) + PLA-CF must issue a NOZZLE WEAR HAZARD warning."""
        pla_cf = FilamentProfileRegistry.get_profile("pla_cf")
        res = SettingsValidator.validate_pairing(self.a1, pla_cf)
        self.assertTrue(res.is_compatible)
        self.assertTrue(any("NOZZLE WEAR HAZARD" in w for w in res.warnings))

    def test_enclosed_hardened_printer_clears_warnings(self):
        """Bambu X1-Carbon (enclosed, hardened nozzle) paired with PA-CF has 0 warnings."""
        pa_cf = FilamentProfileRegistry.get_profile("pa_cf")
        res = SettingsValidator.validate_pairing(self.x1c, pa_cf)
        self.assertTrue(res.is_compatible)
        # Should NOT warn about missing enclosure or nozzle wear
        self.assertFalse(any("ENCLOSURE MISSING" in w for w in res.warnings))
        self.assertFalse(any("NOZZLE WEAR HAZARD" in w for w in res.warnings))
        # Should include drying notes
        self.assertTrue(any("HYGROSCOPIC" in n for n in res.operational_notes))

    def test_thermal_limit_exceeded_error(self):
        """A printer with lower thermal ceilings must produce a hard compatibility error."""
        low_temp_printer = PrinterProfile(
            id="low_temp",
            name="Low Temp Prototype",
            manufacturer="Custom",
            build_volume_x=200.0,
            build_volume_y=200.0,
            build_volume_z=200.0,
            max_nozzle_temp=230.0,  # Below PC requirements (275C)
            max_bed_temp=60.0
        )
        pc = FilamentProfileRegistry.get_profile("pc")
        res = SettingsValidator.validate_pairing(low_temp_printer, pc)
        self.assertFalse(res.is_compatible)
        self.assertFalse(res.is_safe_to_slice)
        self.assertGreater(len(res.errors), 0)
        self.assertTrue(any("Thermal Limit Exceeded" in e for e in res.errors))

if __name__ == "__main__":
    unittest.main()

