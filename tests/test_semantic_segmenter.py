"""
Unit tests for PrintMate non-destructive semantic mesh segmenter.
"""

import unittest
import numpy as np
import trimesh

from printmate.vision.vision_classifier import VisionClassification
from printmate.vision.semantic_detector import SemanticDetector
from printmate.vision.semantic_segmenter import SemanticSegmenter, SegmentedMesh

class TestSemanticSegmenter(unittest.TestCase):

    def setUp(self):
        # 30x30x60 box with subdivided faces
        box = trimesh.creation.box(extents=[30.0, 30.0, 60.0])
        box.apply_translation([0, 0, 30.0])
        self.mesh = box.subdivide()
        self.orig_vertices_count = len(self.mesh.vertices)
        self.orig_faces_count = len(self.mesh.faces)

        self.vis_cls = VisionClassification(
            primary_category="Human Figurine / Deity Idol",
            confidence=0.90,
            detected_classes=[],
            visual_description="Humanoid statue",
            prominent_features=["face", "hands", "pedestal"],
            aesthetic_surfaces=["face", "hands"],
            is_organic_figurine=True
        )
        self.report = SemanticDetector.detect_features(self.mesh, self.vis_cls)

    def test_segmentation_face_partitioning(self):
        segmented = SemanticSegmenter.segment(self.mesh, self.report)

        self.assertIsInstance(segmented, SegmentedMesh)
        self.assertEqual(segmented.total_faces, self.orig_faces_count)

        # Sum of faces in all features must equal total faces
        total_partitioned = sum(len(f_idx) for f_idx in segmented.feature_face_indices.values())
        self.assertEqual(total_partitioned, self.orig_faces_count)

        # Verify geometry was untouched
        self.assertEqual(len(self.mesh.vertices), self.orig_vertices_count)
        self.assertEqual(len(self.mesh.faces), self.orig_faces_count)

    def test_colored_mesh_generation(self):
        segmented = SemanticSegmenter.segment(self.mesh, self.report)
        colored = SemanticSegmenter.generate_colored_mesh(self.mesh, segmented)

        self.assertIsInstance(colored, trimesh.Trimesh)
        self.assertEqual(len(colored.faces), self.orig_faces_count)
        # Check that face colors array exists and has shape (N, 4)
        self.assertEqual(colored.visual.face_colors.shape, (self.orig_faces_count, 4))

    def test_extract_candidate_regions(self):
        segmented = SemanticSegmenter.segment(self.mesh, self.report)
        regions = SemanticSegmenter.extract_candidate_regions(self.mesh, segmented)

        self.assertGreater(len(regions), 0)
        for r_name, r_mesh in regions.items():
            self.assertIsInstance(r_mesh, trimesh.Trimesh)
            self.assertGreater(len(r_mesh.faces), 0)

if __name__ == "__main__":
    unittest.main()
