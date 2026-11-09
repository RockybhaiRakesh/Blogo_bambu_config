"""
Unit tests for PrintMate 3D semantic feature detector.
"""

import unittest
import trimesh

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.semantic_detector import SemanticDetector, SemanticDetectionReport

class TestSemanticDetector(unittest.TestCase):

    def setUp(self):
        # 40x40x100mm synthetic humanoid figurine envelope (Z from 0 to 100)
        self.figurine_mesh = trimesh.creation.box(extents=[40.0, 40.0, 100.0])
        self.figurine_mesh.apply_translation([0, 0, 50.0])

        self.figurine_cls = VisionClassification(
            primary_category="Human Figurine / Deity Idol",
            confidence=0.92,
            detected_classes=[],
            visual_description="Seated figurine",
            prominent_features=["face", "hands", "pedestal"],
            aesthetic_surfaces=["face", "hands"],
            is_organic_figurine=True
        )

        self.mech_cls = VisionClassification(
            primary_category="Mechanical Component",
            confidence=0.88,
            detected_classes=[],
            visual_description="Flange mount",
            prominent_features=["mounting holes"],
            aesthetic_surfaces=["mating face"],
            is_mechanical=True
        )

    def test_figurine_anatomy_detection(self):
        report = SemanticDetector.detect_features(self.figurine_mesh, self.figurine_cls)

        self.assertIsInstance(report, SemanticDetectionReport)
        self.assertTrue(report.has_delicate_anatomy)
        self.assertTrue(report.has_removable_pedestal)
        self.assertIsNotNone(report.recommended_split_zone_z)

        # Check features detected
        feat_names = [f.name for f in report.features]
        self.assertIn("Pedestal / Lotus Base", feat_names)
        self.assertIn("Torso & Main Body", feat_names)
        self.assertIn("Hands & Delicate Limbs", feat_names)
        self.assertIn("Head, Face & Crown", feat_names)

        # Check coordinate bounds validity
        for f in report.features:
            self.assertLess(f.bbox_3d["min_x"], f.bbox_3d["max_x"])
            self.assertLess(f.bbox_3d["min_z"], f.bbox_3d["max_z"])
            self.assertEqual(len(f.center_3d), 3)

    def test_mechanical_component_detection(self):
        report = SemanticDetector.detect_features(self.figurine_mesh, self.mech_cls)
        feat_names = [f.name for f in report.features]
        self.assertIn("Mounting Base / Flange", feat_names)
        self.assertFalse(report.has_delicate_anatomy)

    def test_unknown_object_fallback(self):
        unknown_cls = VisionClassification(
            primary_category="Unknown / Mixed Object",
            confidence=0.50,
            detected_classes=[],
            visual_description="Unknown object",
            prominent_features=[],
            aesthetic_surfaces=[]
        )
        report = SemanticDetector.detect_features(self.figurine_mesh, unknown_cls)
        self.assertEqual(len(report.features), 1)
        self.assertEqual(report.features[0].localization_status, "approximate_geometric")

if __name__ == "__main__":
    unittest.main()

