"""
Semantic Mesh Segmentation module.
Non-destructively assigns mesh faces and vertices to detected semantic regions
and generates colored visual overlays without modifying original topology.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import trimesh

from printmate.vision.semantic_detector import SemanticDetectionReport, SemanticFeature3D

@dataclass
class SegmentedMesh:
    """Non-destructive semantic segmentation labeling for a 3D mesh."""
    total_faces: int
    feature_names: List[str]
    face_counts_per_feature: Dict[str, int]
    feature_face_indices: Dict[str, List[int]] = field(default_factory=dict)
    visual_color_palette: Dict[str, List[int]] = field(default_factory=dict)
    has_unassigned_faces: bool = False

class SemanticSegmenter:
    """Partitions mesh faces into semantic anatomical and functional components."""

    # Default distinct RGBA palette for semantic overlays
    COLOR_PALETTE = {
        "Pedestal / Lotus Base": [80, 160, 240, 255],     # Blue
        "Mounting Base / Flange": [80, 160, 240, 255],
        "Torso & Main Body": [70, 200, 120, 255],          # Green
        "Sculptural Body": [70, 200, 120, 255],
        "Hands & Delicate Limbs": [240, 80, 80, 255],      # Red (Critical fragility)
        "Head, Face & Crown": [255, 190, 50, 255],        # Gold / Yellow
        "Unassigned": [180, 180, 180, 255]                 # Gray
    }

    @classmethod
    def segment(
        cls,
        mesh: trimesh.Trimesh,
        detection_report: SemanticDetectionReport
    ) -> SegmentedMesh:
        """
        Associates each mesh face with a detected semantic feature envelope.

        Args:
            mesh: trimesh.Trimesh instance.
            detection_report: SemanticDetectionReport from SemanticDetector.

        Returns:
            SegmentedMesh dataclass.
        """
        num_faces = len(mesh.faces)
        if num_faces == 0 or not detection_report.features:
            return SegmentedMesh(
                total_faces=num_faces,
                feature_names=[],
                face_counts_per_feature={}
            )

        face_centers = mesh.triangles_center
        face_indices_map: Dict[str, List[int]] = {f.name: [] for f in detection_report.features}
        unassigned_indices: List[int] = []

        # Vectorized bounding box containment check per feature
        assigned = np.zeros(num_faces, dtype=bool)

        # Prioritize delicate features first (hands, head), then torso, then base
        sorted_features = sorted(detection_report.features, key=lambda f: (not f.is_fragile, f.category == "Base"))

        for f in sorted_features:
            bbox = f.bbox_3d
            in_box = (
                (face_centers[:, 0] >= bbox["min_x"]) & (face_centers[:, 0] <= bbox["max_x"]) &
                (face_centers[:, 1] >= bbox["min_y"]) & (face_centers[:, 1] <= bbox["max_y"]) &
                (face_centers[:, 2] >= bbox["min_z"]) & (face_centers[:, 2] <= bbox["max_z"])
            )
            # Only claim faces not already claimed by a higher-priority feature
            claim_mask = in_box & (~assigned)
            claimed_indices = np.where(claim_mask)[0].tolist()
            face_indices_map[f.name].extend(claimed_indices)
            assigned[claim_mask] = True

        # Any unassigned faces are assigned to the closest feature center
        unassigned_count = int(np.sum(~assigned))
        if unassigned_count > 0:
            unassigned_idx = np.where(~assigned)[0]
            feature_centers = np.array([f.center_3d for f in detection_report.features])
            for u_idx in unassigned_idx:
                fc = face_centers[u_idx]
                dists = np.linalg.norm(feature_centers - fc, axis=1)
                closest_feat = detection_report.features[int(np.argmin(dists))]
                face_indices_map[closest_feat.name].append(int(u_idx))

        counts = {name: len(indices) for name, indices in face_indices_map.items()}

        palette = {}
        for name in face_indices_map:
            palette[name] = cls.COLOR_PALETTE.get(name, [150, 150, 150, 255])

        return SegmentedMesh(
            total_faces=num_faces,
            feature_names=list(face_indices_map.keys()),
            face_counts_per_feature=counts,
            feature_face_indices=face_indices_map,
            visual_color_palette=palette,
            has_unassigned_faces=False
        )

    @classmethod
    def generate_colored_mesh(
        cls,
        mesh: trimesh.Trimesh,
        segmented: SegmentedMesh
    ) -> trimesh.Trimesh:
        """
        Creates a copy of the mesh with RGBA face colors reflecting semantic segmentation.
        Preserves original geometry completely.
        """
        mesh_copy = mesh.copy()
        face_colors = np.full((len(mesh.faces), 4), [180, 180, 180, 255], dtype=np.uint8)

        for feat_name, indices in segmented.feature_face_indices.items():
            color = segmented.visual_color_palette.get(feat_name, [150, 150, 150, 255])
            if indices:
                face_colors[indices] = color

        mesh_copy.visual.face_colors = face_colors
        return mesh_copy

    @classmethod
    def extract_candidate_regions(
        cls,
        mesh: trimesh.Trimesh,
        segmented: SegmentedMesh
    ) -> Dict[str, trimesh.Trimesh]:
        """
        Extracts submeshes corresponding to each semantic feature without modifying original mesh.
        """
        regions: Dict[str, trimesh.Trimesh] = {}
        for feat_name, indices in segmented.feature_face_indices.items():
            if len(indices) > 0:
                submesh = mesh.submesh([indices], append=True)
                regions[feat_name] = submesh
        return regions

