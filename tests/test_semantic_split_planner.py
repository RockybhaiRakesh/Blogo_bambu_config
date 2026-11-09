"""
Unit tests for PrintMate semantic split planner.
"""

import unittest
import trimesh

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.semantic_detector import SemanticDetector
from printmate.splitting.semantic_split_planner import SemanticSplitPlanner, SemanticSplitPlan

class TestSemanticSplitPlanner(unittest.TestCase):

    def setUp(self):
        # 40x40x80 figurine box
        self.mesh = trimesh.creation.box(extents=[40.0, 40.0, 80.0])
        self.mesh.apply_translation([0, 0, 40.0])

        self.fig_cls = VisionClassification(
            primary_category="Human Figurine / Deity Idol",
            confidence=0.92,
            detected_classes=[],
            visual_description="Seated divine idol on lotus base",
            prominent_features=["face", "hands", "pedestal"],
            aesthetic_surfaces=["face", "hands"],
            is_organic_figurine=True
        )
        self.det_rep = SemanticDetector.detect_features(self.mesh, self.fig_cls)

    def test_hybrid_split_recommendation_for_figurine(self):
        plan = SemanticSplitPlanner.plan(self.mesh, self.det_rep)

        self.assertIsInstance(plan, SemanticSplitPlan)
        self.assertFalse(plan.model_exceeds_bed)
        self.assertIsNotNone(plan.recommended_strategy)

        # Top strategy should be Hybrid Semantic Split with dowel pins
        rec = plan.recommended_strategy
        self.assertEqual(rec.strategy_type, "hybrid_split")
        self.assertTrue(rec.dowel_connector_feasible)
        self.assertIsNotNone(rec.split_plane_origin)
        self.assertGreater(rec.score, 85.0)

    def test_oversized_model_geometric_split(self):
        # 300mm tall mesh exceeds Bambu A1 256mm build volume
        tall_mesh = trimesh.creation.box(extents=[30.0, 30.0, 300.0])
        tall_mesh.apply_translation([0, 0, 150.0])
        det_rep_tall = SemanticDetector.detect_features(tall_mesh, self.fig_cls)

        plan = SemanticSplitPlanner.plan(tall_mesh, det_rep_tall)
        self.assertTrue(plan.model_exceeds_bed)
        # Should recommend geometric split to fit bed
        self.assertEqual(plan.recommended_strategy.strategy_type, "geometric_split")

    def test_single_piece_option_present(self):
        plan = SemanticSplitPlanner.plan(self.mesh, self.det_rep)
        types = [o.strategy_type for o in plan.ranked_options]
        self.assertIn("single_piece", types)

if __name__ == "__main__":
    unittest.main()

