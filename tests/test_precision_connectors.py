"""
Unit tests for Precision Connector Engineering module (ConnectorGenerator).
"""

import unittest
import shapely.geometry as sg
import trimesh

from printmate.connectors.connector_generator import (
    ConnectorGenerator,
    DowelLockConfig,
    ConnectorType,
    ConnectorValidationResult
)

class TestPrecisionConnectors(unittest.TestCase):

    def test_all_connector_types_geometry(self):
        """Verifies 3D mesh generation and watertightness for all connector types."""
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
                pin_spacing=10.0
            )
            pin_mesh = ConnectorGenerator.create_pin_mesh(cfg, (0, 0, 0))
            socket_mesh = ConnectorGenerator.create_socket_cutter_mesh(cfg, (0, 0, 0))

            self.assertIsInstance(pin_mesh, trimesh.Trimesh, f"Failed for {ctype}")
            self.assertIsInstance(socket_mesh, trimesh.Trimesh, f"Failed for {ctype}")
            self.assertTrue(pin_mesh.is_watertight, f"Pin not watertight for {ctype}")
            self.assertTrue(socket_mesh.is_watertight, f"Socket not watertight for {ctype}")
            # Socket cutter volume must exceed pin volume due to clearances
            self.assertGreater(socket_mesh.volume, pin_mesh.volume, f"Tolerance volume failed for {ctype}")

    def test_wall_thickness_validation(self):
        """Tests minimum wall thickness validation and boundary clipping checks."""
        # 30x30 mm solid square cut face
        plate = sg.box(-15, -15, 15, 15)

        # Centered pin -> min wall is ~12mm
        cfg = DowelLockConfig(connector_type=ConnectorType.D_SHAPED, pin_radius=3.0, min_wall_thickness=2.0)
        res_valid = ConnectorGenerator.validate_placement(plate, (0.0, 0.0), cfg)
        self.assertTrue(res_valid.is_valid)
        self.assertGreater(res_valid.min_wall_found_mm, 10.0)

        # Pin placed near edge (X=13.5) -> wall is only 1.5mm - 0.25 = 1.25mm
        res_invalid = ConnectorGenerator.validate_placement(plate, (13.5, 0.0), cfg)
        self.assertFalse(res_invalid.is_valid)
        self.assertIsNotNone(res_invalid.warning)

    def test_dual_pin_interference_detection(self):
        """Verifies collision check between dual pins when spacing is insufficient."""
        plate = sg.box(-30, -30, 30, 30)
        # Pin radius 3.0mm, spacing 4.0mm -> collision (3 + 3 = 6mm needed)
        cfg_collide = DowelLockConfig(
            connector_type=ConnectorType.DUAL_PIN,
            pin_radius=3.0,
            pin_spacing=4.0
        )
        res = ConnectorGenerator.validate_placement(plate, (0.0, 0.0), cfg_collide)
        self.assertTrue(res.interference_detected)
        self.assertFalse(res.is_valid)

if __name__ == "__main__":
    unittest.main()

