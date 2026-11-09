"""
Vision package for PrintMate AI.
Contains multi-view rendering, visual classification, 2D-to-3D semantic feature
localization, non-destructive mesh segmentation, and UI preview generation.
"""

from printmate.vision.view_renderer import ViewRenderer, RenderView, RenderCollection
from printmate.vision.vision_classifier import VisionClassifier, VisionClassification
from printmate.vision.semantic_detector import SemanticDetector, SemanticFeature3D, SemanticDetectionReport
from printmate.vision.semantic_segmenter import SemanticSegmenter, SegmentedMesh
from printmate.vision.preview_generator import PreviewGenerator, UIPreviewPayload

__all__ = [
    "ViewRenderer",
    "RenderView",
    "RenderCollection",
    "VisionClassifier",
    "VisionClassification",
    "SemanticDetector",
    "SemanticFeature3D",
    "SemanticDetectionReport",
    "SemanticSegmenter",
    "SegmentedMesh",
    "PreviewGenerator",
    "UIPreviewPayload",
]
