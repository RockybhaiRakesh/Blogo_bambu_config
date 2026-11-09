"""
Unit tests for Connector Pair Validator module (ConnectorPairValidator).
"""

import unittest
import shapely.geometry as sg
import trimesh

from printmate.connectors.connector_generator import (
    ConnectorGenerator,
    DowelLockConfig,
    ConnectorType
)
from printmate.connectors.pair_validator import (
    ConnectorPairValidator,
    PairValidationResult
)

class TestPairValidator(unittest.TestCase):

    def setUp(self):
        # Create matching upper and lower box meshes
        self.base_box = trimesh.creation.box(extents=(30.0, 30.0, 20.0))
        self.base_box.apply_translation([0, 0, -10.0]) # Z in [-20, 0]

        self.top_box = trimesh.creation.box(extents=(30.0, 30.0, 20.0))
        self.top_box.apply_translation([0, 0, 10.0])   # Z in [0, 20]

    def test_all_five_connector_types(self):
        """Verifies pair validation across all 5 connector architectures."""
        types = [
            ConnectorType.CYLINDRICAL,
            ConnectorType.D_SHAPED,
            ConnectorType.KEYED,
            ConnectorType.DUAL_PIN,
            ConnectorType.ASYMMETRIC
        ]
        for ctype in types:
            cfg = DowelLockConfig(
                connector_type=ctype,
                pin_radius=3.0,
                pin_height=5.0,
                clearance=0.25,
                pin_spacing=10.0,
                socket_depth_extra=1.0,
                min_wall_thickness=2.0
            )
            res = ConnectorPairValidator.validate_pair(
                male_mesh=self.base_box,
                female_mesh=self.top_box,
                config=cfg,
                z_cut=0.0,
                center_xy=(0.0, 0.0)
            )
            self.assertIsInstance(res, PairValidationResult)
            self.assertTrue(res.is_valid, f"Failed for {ctype}: {res.errors}")
            self.assertAlmostEqual(res.radial_clearance_mm, 0.25)
            self.assertAlmostEqual(res.axial_relief_mm, 1.0)
            self.assertFalse(res.exterior_breakthrough)
            self.assertFalse(res.interference_detected)

    def test_insufficient_clearance_rejection(self):
        """Verifies rejection when radial clearance is below safe FDM threshold."""
        cfg_tight = DowelLockConfig(clearance=0.05) # 0.05mm is below 0.12mm safe limit
        res = ConnectorPairValidator.validate_pair(
            male_mesh=self.base_box,
            female_mesh=self.top_box,
            config=cfg_tight,
            z_cut=0.0
        )
        self.assertFalse(res.is_valid)
        self.assertTrue(any("fusion limit" in err for err in res.errors))

    def test_negative_axial_relief_rejection(self):
        """Verifies rejection when pin would bottom out in socket."""
        cfg_bottoming = DowelLockConfig(socket_depth_extra=0.0) # Zero air gap
        res = ConnectorPairValidator.validate_pair(
            male_mesh=self.base_box,
            female_mesh=self.top_box,
            config=cfg_bottoming,
            z_cut=0.0
        )
        self.assertFalse(res.is_valid)
        self.assertTrue(any("non-positive" in err for err in res.errors))

    def test_exterior_breakthrough_detection(self):
        """Detects critical breakthrough when connector socket exceeds model boundaries."""
        # Small 8x8mm top box with 6mm diameter pin + clearance placed at center
        small_top = trimesh.creation.box(extents=(6.2, 6.2, 20.0))
        small_top.apply_translation([0, 0, 10.0])

        cfg = DowelLockConfig(pin_radius=3.0, clearance=0.25, min_wall_thickness=2.0)
        res = ConnectorPairValidator.validate_pair(
            male_mesh=self.base_box,
            female_mesh=small_top,
            config=cfg,
            z_cut=0.0
        )
        self.assertFalse(res.is_valid)
        self.assertTrue(res.exterior_breakthrough)

if __name__ == "__main__":
    unittest.main()

