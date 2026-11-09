"""
Unit tests for PrintMate strategic decision engine.
"""

import unittest
import trimesh

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.semantic_detector import SemanticDetector
from printmate.splitting.semantic_split_planner import SemanticSplitPlanner
from printmate.intelligence.decision_engine import DecisionEngine, StrategicPrintPlan

class TestDecisionEngine(unittest.TestCase):

    def setUp(self):
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
        self.split_plan = SemanticSplitPlanner.plan(self.mesh, self.det_rep)

    def test_decision_synthesis(self):
        plan = DecisionEngine.evaluate(
            classification=self.fig_cls,
            semantic_report=self.det_rep,
            split_plan=self.split_plan,
            filament="pla_basic"
        )

        self.assertIsInstance(plan, StrategicPrintPlan)
        self.assertGreaterEqual(plan.confidence, 0.8)
        self.assertGreater(len(plan.ranked_strategies), 0)
        self.assertIn("nozzle_diameter", plan.slicer_profile_overrides)
        self.assertIn("layer_height", plan.slicer_profile_overrides)

    def test_user_interaction_prompt_trigger(self):
        # When competing strategies are close in score, engine prompts the user
        plan = DecisionEngine.evaluate(
            classification=self.fig_cls,
            semantic_report=self.det_rep,
            split_plan=self.split_plan,
            filament="pla_basic"
        )

        if plan.user_decision_required:
            self.assertGreater(len(plan.pending_questions), 0)
            q = plan.pending_questions[0]
            self.assertEqual(q.question_id, "split_vs_single")
            self.assertIn("Hybrid Split", q.recommended_option)

if __name__ == "__main__":
    unittest.main()

