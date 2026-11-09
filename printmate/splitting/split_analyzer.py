"""
Split plane analysis module.
Scans 3D mesh cross-sections along axes to identify optimal low-visibility,
high-stability cut locations (e.g. waistlines, pedestal transitions).
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import trimesh

class SplitAnalyzer:
    """Analyzes geometric profiles to recommend intelligent cut planes."""

    @staticmethod
    def sample_cross_sections(
        mesh: trimesh.Trimesh,
        axis: int = 2,
        num_samples: int = 50
    ) -> List[Dict[str, float]]:
        """
        Samples cross-sections along an axis and measures bounding envelope and perimeter.

        Args:
            mesh: Trimesh instance.
            axis: Axis index (0=X, 1=Y, 2=Z).
            num_samples: Number of sampling steps.

        Returns:
            List of dicts with height and cross-section envelope metrics.
        """
        bounds = mesh.bounds
        min_val = bounds[0][axis]
        max_val = bounds[1][axis]
        step = (max_val - min_val) / (num_samples + 1)

        samples: List[Dict[str, float]] = []
        normal = [0.0, 0.0, 0.0]
        normal[axis] = 1.0

        for i in range(1, num_samples + 1):
            pos = min_val + i * step
            origin = [0.0, 0.0, 0.0]
            origin[axis] = pos
            try:
                section = mesh.section(plane_origin=origin, plane_normal=normal)
                if section is not None:
                    # Projected 2D area or bounding extent
                    samples.append({
                        "pos": round(float(pos), 2),
                        "length": round(float(section.length), 2),
                    })
            except Exception:
                continue

        return samples

    @staticmethod
    def find_necking_candidates(
        samples: List[Dict[str, float]],
        min_margin_ratio: float = 0.15
    ) -> List[float]:
        """
        Finds local minima in cross-section perimeter/length, indicating natural waistlines.

        Args:
            samples: List of cross-section sample metrics.
            min_margin_ratio: Margin from top and bottom boundaries to ignore extremities.

        Returns:
            List of suggested cut positions.
        """
        if len(samples) < 5:
            return []

        n = len(samples)
        start_idx = int(n * min_margin_ratio)
        end_idx = int(n * (1.0 - min_margin_ratio))

        candidates: List[float] = []
        for i in range(start_idx, end_idx):
            prev_l = samples[i - 1]["length"]
            curr_l = samples[i]["length"]
            next_l = samples[i + 1]["length"]

            # Local minimum in perimeter
            if curr_l < prev_l and curr_l < next_l and curr_l > 0.1:
                candidates.append(samples[i]["pos"])

        return candidates

