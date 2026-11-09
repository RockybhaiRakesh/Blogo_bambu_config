"""
Unit tests for PrintMate multi-view snapshot renderer.
"""

import os
import unittest
import tempfile
import trimesh

from printmate.vision.view_renderer import ViewRenderer, RenderCollection

class TestViewRenderer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_render_")
        self.cube = trimesh.creation.box(extents=[15.0, 20.0, 25.0])

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_canonical_views_generation(self):
        # Render using software/matplotlib engine for fast deterministic unit test
        renders = ViewRenderer.render_views(
            model_input=self.cube,
            output_dir=self.temp_dir,
            resolution=(200, 200),
            engine="matplotlib"
        )

        self.assertIsInstance(renders, RenderCollection)
        expected_views = ["front", "back", "left", "right", "top", "isometric"]
        for v in expected_views:
            self.assertIn(v, renders.views)
            v_info = renders.views[v]
            self.assertTrue(os.path.exists(v_info.image_path))
            self.assertGreater(os.path.getsize(v_info.image_path), 0)
            self.assertEqual(len(v_info.camera_pos), 3)

    def test_caching_behavior(self):
        renders1 = ViewRenderer.render_views(
            model_input=self.cube,
            output_dir=self.temp_dir,
            resolution=(200, 200),
            engine="matplotlib"
        )
        mod_time_1 = os.path.getmtime(renders1.views["front"].image_path)

        # Re-rendering without force_rerender should hit cache
        renders2 = ViewRenderer.render_views(
            model_input=self.cube,
            output_dir=self.temp_dir,
            resolution=(200, 200),
            engine="matplotlib",
            force_rerender=False
        )
        mod_time_2 = os.path.getmtime(renders2.views["front"].image_path)
        self.assertEqual(mod_time_1, mod_time_2)

if __name__ == "__main__":
    unittest.main()

