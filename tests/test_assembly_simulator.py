"""
Unit tests for Assembly Simulator and Reconstruction module (AssemblySimulator).
"""

import unittest
import trimesh

from printmate.assembly.assembly_simulator import (
    AssemblySimulator,
    AssemblyValidationReport
)

class TestAssemblySimulator(unittest.TestCase):

    def setUp(self):
        # 40x40x60 mm reference box
        self.original_box = trimesh.creation.box(extents=(40.0, 40.0, 60.0))
        # Part 1 (lower half, Z in [-30, 0])
        self.part1 = trimesh.creation.box(extents=(40.0, 40.0, 30.0))
        self.part1.apply_translation([0, 0, -15.0])
        # Part 2 (upper half, Z in [0, 30])
        self.part2 = trimesh.creation.box(extents=(40.0, 40.0, 30.0))
        self.part2.apply_translation([0, 0, 15.0])

    def test_clean_assembly_reconstruction(self):
        """Verifies perfect reconstruction of cleanly split parts against original model."""
        rep = AssemblySimulator.simulate_assembly(
            parts=[self.part1, self.part2],
            original_mesh=self.original_box,
            expected_part_count=2
        )
        self.assertIsInstance(rep, AssemblyValidationReport)
        self.assertTrue(rep.is_valid)
        self.assertAlmostEqual(rep.bounds_max_delta_mm, 0.0, places=3)
        self.assertFalse(rep.gaps_detected)
        self.assertFalse(rep.overlaps_detected)

    def test_missing_part_detection(self):
        """Verifies failure when one or more expected sub-parts are missing."""
        rep = AssemblySimulator.simulate_assembly(
            parts=[self.part1],
            expected_part_count=2
        )
        self.assertFalse(rep.is_valid)
        self.assertTrue(any("Part count mismatch" in err for err in rep.errors))

    def test_interfacial_gap_detection(self):
        """Detects physical gap when parts do not touch along parting plane."""
        # Shift part 2 upward by 2.0mm
        part2_shifted = self.part2.copy()
        part2_shifted.apply_translation([0, 0, 2.0])

        rep = AssemblySimulator.simulate_assembly(
            parts=[self.part1, part2_shifted],
            expected_part_count=2
        )
        self.assertTrue(rep.gaps_detected)
        self.assertGreater(rep.max_gap_mm, 1.5)

    def test_interfacial_overlap_detection(self):
        """Detects collision/interference when parts overlap along Z axis."""
        # Shift part 2 downward into part 1 by 1.5mm
        part2_overlap = self.part2.copy()
        part2_overlap.apply_translation([0, 0, -1.5])

        rep = AssemblySimulator.simulate_assembly(
            parts=[self.part1, part2_overlap],
            expected_part_count=2
        )
        self.assertTrue(rep.overlaps_detected)
        self.assertGreater(rep.max_overlap_mm, 1.0)

if __name__ == "__main__":
    unittest.main()

