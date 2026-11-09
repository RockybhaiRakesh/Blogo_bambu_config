"""
Wall thickness analysis module.
Performs ray-based local wall thickness sampling across 3D meshes to detect
fragile, unprintable, or sub-perimeter thin-wall regions for FDM slicing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import trimesh

@dataclass
class ThicknessReport:
    """Summary of local wall thickness measurements and thin-wall risks."""
    min_thickness: float
    max_thickness: float
    mean_thickness: float
    median_thickness: float
    samples_evaluated: int
    critical_threshold_mm: float      # E.g., 0.4mm (single nozzle width)
    caution_threshold_mm: float       # E.g., 0.8mm (double perimeter recommended)
    critical_samples_count: int       # Below critical threshold (<0.4mm)
    caution_samples_count: int        # Between critical and caution (0.4mm - 0.8mm)
    thin_sample_coordinates: List[List[float]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class ThicknessAnalyzer:
    """Measures local geometric wall thickness using inward normal ray-casting."""

    @classmethod
    def analyze(
        cls,
        mesh: trimesh.Trimesh,
        sample_count: int = 500,
        nozzle_diameter: float = 0.4,
        caution_factor: float = 2.0,
        max_ray_dist: float = 100.0
    ) -> ThicknessReport:
        """
        Samples wall thickness across the mesh by casting inward rays from surface faces.

        Args:
            mesh: Watertight or surface trimesh.Trimesh.
            sample_count: Number of surface points/faces to sample.
            nozzle_diameter: Nozzle extrusion width baseline (0.4mm for Bambu A1).
            caution_factor: Multiplier for safe perimeter thickness (default 2.0x = 0.8mm).
            max_ray_dist: Maximum ray distance to avoid infinite voids.

        Returns:
            ThicknessReport dataclass.
        """
        critical_threshold = float(nozzle_diameter)
        caution_threshold = float(nozzle_diameter * caution_factor)

        if len(mesh.faces) == 0:
            return ThicknessReport(
                min_thickness=0.0,
                max_thickness=0.0,
                mean_thickness=0.0,
                median_thickness=0.0,
                samples_evaluated=0,
                critical_threshold_mm=critical_threshold,
                caution_threshold_mm=caution_threshold,
                critical_samples_count=0,
                caution_samples_count=0,
                warnings=["Empty mesh provided; thickness analysis skipped."]
            )

        # Select sampling face indices (keep safe sample count to prevent excessive RAM on dense models)
        num_faces = len(mesh.faces)
        # On very large meshes (>25,000 triangles), cap sample count to 100 rays to guarantee <50MB RAM
        safe_sample_limit = 100 if num_faces > 25000 else sample_count
        actual_samples = min(safe_sample_limit, num_faces)
        
        # Use deterministic or evenly spaced indices for reproducibility
        if actual_samples < num_faces:
            face_indices = np.linspace(0, num_faces - 1, actual_samples, dtype=int)
        else:
            face_indices = np.arange(num_faces)

        face_centers = mesh.triangles_center[face_indices]
        face_normals = mesh.face_normals[face_indices]

        # Offset slightly inward to prevent self-intersection with the originating face
        epsilon = 1e-4
        ray_origins = face_centers - face_normals * epsilon
        ray_directions = -face_normals  # Inward direction

        measured_thicknesses: List[float] = []
        thin_coords: List[List[float]] = []

        # Execute ray casting in small chunks (batch_size=20) to prevent trimesh numpy ArrayMemoryError
        batch_size = 20
        for b_start in range(0, len(ray_origins), batch_size):
            b_origins = ray_origins[b_start : b_start + batch_size]
            b_dirs = ray_directions[b_start : b_start + batch_size]
            try:
                index_tri, index_ray, locations = mesh.ray.intersects_id(
                    ray_origins=b_origins,
                    ray_directions=b_dirs,
                    return_locations=True
                )
                if len(index_ray) > 0:
                    for hit_idx, local_ray_idx in enumerate(index_ray):
                        origin = b_origins[local_ray_idx]
                        hit_loc = locations[hit_idx]
                        dist = float(np.linalg.norm(hit_loc - origin))

                        if 0.001 < dist <= max_ray_dist:
                            measured_thicknesses.append(dist)
                            if dist < caution_threshold:
                                thin_coords.append([round(float(c), 3) for c in origin])
            except Exception:
                # Silently skip batch if trimesh encounters ray collision issues on damaged geometry
                continue

        if not measured_thicknesses:
            # Fallback if ray casting encountered no internal intersections (e.g. open surface)
            return ThicknessReport(
                min_thickness=0.0,
                max_thickness=0.0,
                mean_thickness=0.0,
                median_thickness=0.0,
                samples_evaluated=0,
                critical_threshold_mm=critical_threshold,
                caution_threshold_mm=caution_threshold,
                critical_samples_count=0,
                caution_samples_count=0,
                warnings=["No internal opposing surface intersections detected; mesh may be open or non-manifold."]
            )

        thickness_arr = np.array(measured_thicknesses)
        min_thick = float(np.min(thickness_arr))
        max_thick = float(np.max(thickness_arr))
        mean_thick = float(np.mean(thickness_arr))
        median_thick = float(np.median(thickness_arr))

        critical_count = int(np.sum(thickness_arr < critical_threshold))
        caution_count = int(np.sum((thickness_arr >= critical_threshold) & (thickness_arr < caution_threshold)))

        warnings: List[str] = []
        if critical_count > 0:
            pct = (critical_count / len(thickness_arr)) * 100
            warnings.append(
                f"Critical Thin Walls: {critical_count} sample points ({pct:.1f}%) have thickness < {critical_threshold:.2f}mm "
                f"(below 0.4mm nozzle diameter). These regions cannot be sliced as solid perimeters and may vanish or leave holes."
            )

        if caution_count > 0:
            pct = (caution_count / len(thickness_arr)) * 100
            warnings.append(
                f"Sub-Perimeter Thin Walls: {caution_count} sample points ({pct:.1f}%) have thickness between "
                f"{critical_threshold:.2f}mm and {caution_threshold:.2f}mm. Requires Arachne perimeter generator to avoid gaps."
            )

        return ThicknessReport(
            min_thickness=round(min_thick, 3),
            max_thickness=round(max_thick, 3),
            mean_thickness=round(mean_thick, 3),
            median_thickness=round(median_thick, 3),
            samples_evaluated=len(thickness_arr),
            critical_threshold_mm=critical_threshold,
            caution_threshold_mm=caution_threshold,
            critical_samples_count=critical_count,
            caution_samples_count=caution_count,
            thin_sample_coordinates=thin_coords[:50],  # Top 50 coordinates for reporting
            warnings=warnings
        )

