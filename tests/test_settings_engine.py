"""
Unit tests for Intelligent Print Settings Engine (SettingsEngine).
"""

import unittest
from printmate.optimization.settings_engine import (
    SettingsEngine,
    OptimizationObjective,
    OptimizedSettings
)
from printmate.profiles.printer_profiles import PrinterProfileRegistry
from printmate.profiles.filament_profiles import FilamentProfileRegistry

class DummyModelInfo:
    def __init__(self, dim_z: float = 120.0, volume_cm3: float = 150.0):
        self.dim_z = dim_z
        self.volume_cm3 = volume_cm3

class TestSettingsEngine(unittest.TestCase):

    def test_all_optimization_objectives(self):
        """Verifies process parameter tuning across all 6 optimization objectives."""
        info = DummyModelInfo(dim_z=120.0, volume_cm3=150.0)

        # 1. Fine Detail
        s_fine = SettingsEngine.optimize(info, objective=OptimizationObjective.FINE_DETAIL)
        self.assertEqual(s_fine.layer_height, 0.12)
        self.assertEqual(s_fine.wall_loops, 3)
        self.assertEqual(s_fine.wall_generator, "arachne")
        self.assertIn("layer_height", s_fine.reasoning)

        # 2. Strong Functional
        s_strong = SettingsEngine.optimize(info, objective=OptimizationObjective.STRONG_FUNCTIONAL)
        self.assertEqual(s_strong.layer_height, 0.20)
        self.assertEqual(s_strong.wall_loops, 5)
        self.assertEqual(s_strong.sparse_infill_pattern, "gyroid")
        self.assertEqual(s_strong.sparse_infill_density, "35%")
        self.assertIn("wall_loops", s_strong.reasoning)

        # 3. Fast Printing
        s_fast = SettingsEngine.optimize(info, objective=OptimizationObjective.FAST_PRINTING)
        self.assertEqual(s_fast.layer_height, 0.28)
        self.assertEqual(s_fast.wall_loops, 2)
        self.assertEqual(s_fast.sparse_infill_pattern, "grid")

        # 4. Minimum Material
        s_min = SettingsEngine.optimize(info, objective=OptimizationObjective.MINIMUM_MATERIAL)
        self.assertEqual(s_min.sparse_infill_pattern, "adaptive_cubic")
        self.assertEqual(s_min.sparse_infill_density, "8%")

        # 5. Support Minimized
        s_supp = SettingsEngine.optimize(info, objective=OptimizationObjective.SUPPORT_MINIMIZED)
        self.assertEqual(s_supp.support_threshold_angle, 30)

        # 6. Balanced Quality
        s_bal = SettingsEngine.optimize(info, objective=OptimizationObjective.BALANCED_QUALITY)
        self.assertEqual(s_bal.layer_height, 0.16)
        self.assertEqual(s_bal.wall_loops, 3)

    def test_connector_wall_reinforcement(self):
        """Verifies that split parts with connectors have wall loops reinforced to >= 4."""
        info = DummyModelInfo(dim_z=120.0, volume_cm3=150.0)
        # By default balanced has 3 walls
        s_default = SettingsEngine.optimize(info, has_connectors=False)
        self.assertEqual(s_default.wall_loops, 3)

        # With connectors, wall loops must be boosted to 4 for hoop strength
        s_conn = SettingsEngine.optimize(info, has_connectors=True)
        self.assertGreaterEqual(s_conn.wall_loops, 4)
        self.assertIn("connectors", s_conn.reasoning)

    def test_miniature_scale_detection(self):
        """Verifies that models < 65mm in height are capped to <= 0.12mm layer height."""
        mini_info = DummyModelInfo(dim_z=45.0, volume_cm3=20.0)
        s_mini = SettingsEngine.optimize(mini_info, objective=OptimizationObjective.BALANCED_QUALITY)
        self.assertLessEqual(s_mini.layer_height, 0.12)
        self.assertIn("miniature_scale", s_mini.reasoning)

    def test_split_flat_support_elimination(self):
        """Verifies that planar split parts resting flat have support structures disabled."""
        info = DummyModelInfo(dim_z=100.0, volume_cm3=100.0)
        s_flat = SettingsEngine.optimize(info, is_split_flat=True)
        self.assertFalse(s_flat.enable_support)
        self.assertIn("support_mode", s_flat.reasoning)

    def test_to_slicer_overrides_format(self):
        """Verifies conversion of OptimizedSettings to Bambu Studio project JSON overrides."""
        info = DummyModelInfo()
        s = SettingsEngine.optimize(info, objective=OptimizationObjective.BALANCED_QUALITY)
        overrides = s.to_slicer_overrides()

        self.assertIsInstance(overrides, dict)
        self.assertIn("layer_height", overrides)
        self.assertIn("wall_loops", overrides)
        self.assertIn("sparse_infill_density", overrides)
        self.assertIn("sparse_infill_pattern", overrides)
        self.assertIn("outer_wall_speed", overrides)
        self.assertIn("enable_support", overrides)
        self.assertIn("support_type", overrides)
        self.assertIn("nozzle_temperature", overrides)
        self.assertIn("hot_plate_temp", overrides)

    def test_mathematical_heuristic_estimates(self):
        """Verifies mathematical heuristic calculation for print duration and material mass."""
        info = DummyModelInfo(dim_z=100.0, volume_cm3=80.0)
        s = SettingsEngine.optimize(info)
        self.assertGreater(s.estimated_print_time_mins, 0.0)
        self.assertGreater(s.estimated_filament_grams, 0.0)

if __name__ == "__main__":
    unittest.main()
