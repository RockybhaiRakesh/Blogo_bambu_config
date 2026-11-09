"""
Unit tests for Printer Profile Architecture (PrinterProfileRegistry).
"""

import unittest
from printmate.profiles.printer_profiles import (
    PrinterProfileRegistry,
    PrinterProfile,
    ProfileProvenance
)

class TestPrinterProfiles(unittest.TestCase):

    def test_bambu_a1_baseline(self):
        """Verifies validated hardware profile for Bambu Lab A1."""
        profile = PrinterProfileRegistry.get_profile("Bambu Lab A1")
        self.assertIsInstance(profile, PrinterProfile)
        self.assertEqual(profile.name, "Bambu Lab A1")
        self.assertEqual(profile.build_volume_x, 256.0)
        self.assertEqual(profile.build_volume_y, 256.0)
        self.assertEqual(profile.build_volume_z, 256.0)
        self.assertEqual(profile.default_nozzle_diameter, 0.4)
        self.assertEqual(profile.max_nozzle_temp, 300.0)
        self.assertEqual(profile.max_bed_temp, 100.0)
        self.assertFalse(profile.has_enclosure)
        self.assertEqual(profile.provenance, ProfileProvenance.MANUFACTURER_VERIFIED)

    def test_multi_printer_retrieval(self):
        """Verifies multi-vendor printer profiles: Bambu X1-C, Prusa MK4, Creality K1, Ender 3 V3, Anycubic."""
        printers = [
            "Bambu Lab X1-Carbon",
            "Prusa MK4",
            "Creality K1",
            "Creality Ender 3 V3",
            "Anycubic Kobra 2"
        ]
        for name in printers:
            p = PrinterProfileRegistry.get_profile(name)
            self.assertIsInstance(p, PrinterProfile)
            self.assertGreater(p.build_volume_x, 200.0)
            self.assertGreater(p.max_nozzle_temp, 250.0)

    def test_printer_fallback_to_a1(self):
        """Verifies that an unrecognized printer name falls back gracefully to Bambu Lab A1."""
        p = PrinterProfileRegistry.get_profile("Unknown Printer Model 9000")
        self.assertEqual(p.id, "bambu_lab_a1")

    def test_is_material_supported(self):
        """Verifies machine constraint checks for enclosure and abrasive requirements."""
        a1 = PrinterProfileRegistry.get_profile("Bambu Lab A1")
        x1c = PrinterProfileRegistry.get_profile("Bambu Lab X1-Carbon")

        # A1 supports standard PLA and PETG
        self.assertTrue(a1.is_material_supported("pla_basic"))
        self.assertTrue(a1.is_material_supported("petg"))
        # A1 lacks enclosure and hardened nozzle by default
        self.assertFalse(a1.is_material_supported("abs"))
        self.assertFalse(a1.is_material_supported("pa_cf"))

        # X1C has enclosure and hardened nozzle
        self.assertTrue(x1c.is_material_supported("abs"))
        self.assertTrue(x1c.is_material_supported("pa_cf"))

    def test_custom_printer_registration(self):
        """Verifies registering a custom printer."""
        custom = PrinterProfile(
            id="voron_24_350",
            name="Voron 2.4 350mm",
            manufacturer="Voron Design",
            build_volume_x=350.0,
            build_volume_y=350.0,
            build_volume_z=350.0,
            has_enclosure=True,
            has_hardened_nozzle=True,
            provenance=ProfileProvenance.USER_CALIBRATED
        )
        PrinterProfileRegistry.register_profile(custom, overwrite=True)
        retrieved = PrinterProfileRegistry.get_profile("voron_24_350")
        self.assertEqual(retrieved.name, "Voron 2.4 350mm")
        self.assertEqual(retrieved.build_volume_x, 350.0)

if __name__ == "__main__":
    unittest.main()
