"""
Unit tests for PrintMate vision classifier.
"""

import os
import unittest
import tempfile
from PIL import Image

from printmate.vision.vision_classifier import VisionClassifier, VisionClassification

class TestVisionClassifier(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_vis_")
        # Create synthetic test images
        self.figurine_img = os.path.join(self.temp_dir, "ayyappan_idol_front.png")
        self.mech_img = os.path.join(self.temp_dir, "gear_bracket_front.png")
        self.jewel_img = os.path.join(self.temp_dir, "gold_ring_pendant_front.png")
        self.unknown_img = os.path.join(self.temp_dir, "abstract_shape_front.png")

        for p in [self.figurine_img, self.mech_img, self.jewel_img, self.unknown_img]:
            im = Image.new("RGB", (100, 100), color=(200, 200, 200))
            im.save(p)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_figurine_classification(self):
        result = VisionClassifier.classify(
            image_inputs=[self.figurine_img],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertIsInstance(result, VisionClassification)
        self.assertIn("Figurine", result.primary_category)
        self.assertTrue(result.is_organic_figurine)
        self.assertGreaterEqual(result.confidence, 0.8)
        self.assertIn("face", result.aesthetic_surfaces)

    def test_mechanical_classification(self):
        result = VisionClassifier.classify(
            image_inputs=[self.mech_img],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertTrue(result.is_mechanical)
        self.assertIn("Mechanical", result.primary_category)

    def test_jewellery_classification(self):
        result = VisionClassifier.classify(
            image_inputs=[self.jewel_img],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertTrue(result.is_jewellery)
        self.assertIn("Jewellery", result.primary_category)

    def test_empty_input_graceful_handling(self):
        result = VisionClassifier.classify(
            image_inputs=[],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertEqual(result.primary_category, "Unknown / Mixed Object")
        self.assertEqual(result.confidence, 0.0)

    def test_caching_mechanism(self):
        res1 = VisionClassifier.classify(
            image_inputs=[self.unknown_img],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertFalse(res1.cached)

        # Second call should be served from cache
        res2 = VisionClassifier.classify(
            image_inputs=[self.unknown_img],
            provider="local",
            cache_dir=self.temp_dir
        )
        self.assertTrue(res2.cached)
        self.assertEqual(res1.primary_category, res2.primary_category)

if __name__ == "__main__":
    unittest.main()

