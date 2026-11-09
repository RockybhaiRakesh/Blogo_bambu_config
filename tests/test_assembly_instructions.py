"""
Unit tests for Assembly Instructions and Step-by-Step Guidance (AssemblyInstructionsGenerator).
"""

import os
import shutil
import tempfile
import unittest

from printmate.assembly.assembly_instructions import (
    AssemblyInstructionsGenerator,
    AssemblyManual,
    AssemblyStep
)

class TestAssemblyInstructions(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_manual_d_shaped(self):
        """Verifies step-by-step instructions generation for D-shaped connectors."""
        parts = ["models/split_parts/Ayyappan_Part1_Base.stl", "models/split_parts/Ayyappan_Part2_Idol.stl"]
        out_md = os.path.join(self.temp_dir, "manual.md")

        manual = AssemblyInstructionsGenerator.generate_instructions(
            model_name="Lord Ayyappan",
            parts=parts,
            connector_type="d_shaped",
            output_path=out_md
        )
        self.assertIsInstance(manual, AssemblyManual)
        self.assertEqual(manual.total_components, 2)
        self.assertEqual(len(manual.steps), 1)

        step = manual.steps[0]
        self.assertEqual(step.step_number, 1)
        self.assertIn("Ayyappan_Part1_Base.stl", step.base_component)
        self.assertIn("Ayyappan_Part2_Idol.stl", step.mating_component)
        self.assertFalse(step.adhesive_required)
        self.assertIn("flat face", step.angular_keying_rule)

        # Check written file
        self.assertTrue(os.path.exists(out_md))
        with open(out_md, "r", encoding="utf-8") as f:
            text = f.read()
            self.assertIn("Lord Ayyappan", text)
            self.assertIn("Bill of Materials", text)
            self.assertIn("Step 1:", text)

    def test_generate_manual_cylindrical_requires_glue(self):
        """Verifies that cylindrical connectors flag adhesive as recommended."""
        parts = ["PartA.stl", "PartB.stl"]
        manual = AssemblyInstructionsGenerator.generate_instructions(
            model_name="Test Cylindrical",
            parts=parts,
            connector_type="cylindrical"
        )
        self.assertTrue(manual.steps[0].adhesive_required)
        self.assertIn("CA glue", manual.steps[0].bonding_guidance)

if __name__ == "__main__":
    unittest.main()

