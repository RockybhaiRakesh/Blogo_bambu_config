"""
Unit tests for End-to-End Workflow Orchestrator Phase 3 capabilities.
"""

import os
import shutil
import tempfile
import unittest
import trimesh

from printmate.workflow.orchestrator import WorkflowOrchestrator

class TestOrchestratorPhase3(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = WorkflowOrchestrator(verbose=False)

        # Create a test miniature model
        self.box = trimesh.creation.box(extents=(30, 30, 40))
        self.box_path = os.path.join(self.temp_dir, "test_box.stl")
        self.box.export(self.box_path)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_end_to_end_single_piece(self):
        """Tests unified workflow execution in single piece mode."""
        out_3mf = os.path.join(self.temp_dir, "box_out.3mf")
        res = self.orchestrator.run_end_to_end(
            model_path=self.box_path,
            output_3mf=out_3mf,
            mode="single",
            auto_confirm=True,
            launch=False
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["strategy"], "single")
        self.assertTrue(os.path.exists(out_3mf))
        self.assertTrue(os.path.exists(res["report_file"]))
        self.assertTrue(res["validation"].is_valid)

if __name__ == "__main__":
    unittest.main()

