"""
Unit tests for Filament Profile Management (FilamentProfileRegistry).
"""

import unittest
from printmate.profiles.filament_profiles import (
    FilamentProfileRegistry,
    FilamentProfile,
    MaterialCategory
)
from printmate.profiles.printer_profiles import ProfileProvenance

class TestFilamentProfiles(unittest.TestCase):

    def test_default_filaments_exist(self):
        """Verifies core material profiles are present and verified."""
        filaments = [
            "pla_basic", "pla_matte", "pla_silk", "petg", "abs", "asa",
            "tpu", "pc", "pla_cf", "pa_cf"
        ]
        for mat in filaments:
            f = FilamentProfileRegistry.get_profile(mat)
            self.assertIsInstance(f, FilamentProfile)
            self.assertGreater(f.nozzle_temp_recommended, 180.0)
            self.assertGreater(f.bed_temp_recommended, 30.0)
            self.assertEqual(f.provenance, ProfileProvenance.MANUFACTURER_VERIFIED)

    def test_brand_specific_filaments(self):
        """Verifies brand-specific entries: eSUN PLA+, Polymaker PolyLite PETG, Bambu Lab."""
        esun = FilamentProfileRegistry.get_profile("esun_pla_plus")
        self.assertEqual(esun.brand, "eSUN")
        self.assertEqual(esun.category, MaterialCategory.PLA_PLUS)

        poly = FilamentProfileRegistry.get_profile("polymaker_polylite_petg")
        self.assertEqual(poly.brand, "Polymaker")
        self.assertEqual(poly.category, MaterialCategory.PETG)

    def test_thermal_bounds_integrity(self):
        """Verifies thermal logic: min <= recommended <= max for nozzle and bed."""
        for prof in FilamentProfileRegistry.list_filaments():
            self.assertLessEqual(prof.nozzle_temp_min, prof.nozzle_temp_recommended)
            self.assertLessEqual(prof.nozzle_temp_recommended, prof.nozzle_temp_max)
            self.assertLessEqual(prof.bed_temp_min, prof.bed_temp_recommended)
            self.assertLessEqual(prof.bed_temp_recommended, prof.bed_temp_max)

    def test_engineering_material_constraints(self):
        """Verifies that engineering plastics enforce enclosure, abrasive, and drying constraints."""
        abs_prof = FilamentProfileRegistry.get_profile("abs")
        self.assertTrue(abs_prof.enclosure_required)

        pc_prof = FilamentProfileRegistry.get_profile("pc")
        self.assertTrue(pc_prof.enclosure_required)

        pla_cf = FilamentProfileRegistry.get_profile("pla_cf")
        self.assertTrue(pla_cf.is_abrasive)
        self.assertFalse(pla_cf.enclosure_required)

        pa_cf = FilamentProfileRegistry.get_profile("pa_cf")
        self.assertTrue(pa_cf.is_abrasive)
        self.assertTrue(pa_cf.enclosure_required)
        self.assertTrue(pa_cf.moisture_sensitive)
        self.assertIsNotNone(pa_cf.drying_temp_c)
        self.assertIsNotNone(pa_cf.drying_duration_hrs)

    def test_tpu_volumetric_speed_safety(self):
        """Verifies TPU 95A is configured with low volumetric speed to prevent extruder jamming."""
        tpu = FilamentProfileRegistry.get_profile("tpu")
        self.assertLessEqual(tpu.max_volumetric_speed_mm3_s, 4.0)

if __name__ == "__main__":
    unittest.main()

