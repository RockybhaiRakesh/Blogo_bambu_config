"""
Unit tests for Material and Printer-Aware Tolerance Profiles (ToleranceManager).
"""

import unittest
from printmate.connectors.tolerance_profiles import ToleranceManager, ToleranceProfile

class TestToleranceProfiles(unittest.TestCase):

    def test_default_profiles_exist(self):
        """Verifies baseline profiles for PLA Basic, Matte, Silk, and PETG on Bambu Lab A1."""
        materials = ["pla_basic", "pla_matte", "pla_silk", "petg"]
        for mat in materials:
            p_slip = ToleranceManager.get_profile(material=mat, fit_class="slip_fit")
            self.assertIsInstance(p_slip, ToleranceProfile)
            self.assertEqual(p_slip.printer_model, "Bambu Lab A1")
            self.assertEqual(p_slip.material, mat)
            self.assertGreaterEqual(p_slip.radial_clearance, 0.20)
            self.assertLessEqual(p_slip.radial_clearance, 0.35)
            # Must initially be marked theoretical / uncalibrated
            self.assertFalse(p_slip.is_physically_calibrated)

    def test_fit_classes(self):
        """Verifies clearance hierarchy: press_fit < slip_fit < loose_fit."""
        p_press = ToleranceManager.get_profile(material="pla_basic", fit_class="press_fit")
        p_slip = ToleranceManager.get_profile(material="pla_basic", fit_class="slip_fit")
        p_loose = ToleranceManager.get_profile(material="pla_basic", fit_class="loose_fit")

        self.assertLess(p_press.radial_clearance, p_slip.radial_clearance)
        self.assertLess(p_slip.radial_clearance, p_loose.radial_clearance)

    def test_register_calibrated_profile(self):
        """Tests updating a profile with verified physical test coupon results."""
        cal_prof = ToleranceProfile(
            printer_model="Bambu Lab A1",
            nozzle_diameter=0.4,
            material="pla_custom",
            fit_class="slip_fit",
            radial_clearance=0.23,
            axial_relief=0.90,
            notes="Calibrated with gauge slot 2"
        )
        ToleranceManager.register_calibrated_profile(cal_prof)

        retrieved = ToleranceManager.get_profile(material="pla_custom", fit_class="slip_fit")
        self.assertTrue(retrieved.is_physically_calibrated)
        self.assertAlmostEqual(retrieved.radial_clearance, 0.23)

if __name__ == "__main__":
    unittest.main()

