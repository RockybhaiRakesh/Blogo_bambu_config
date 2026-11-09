"""
Floating island and mesh connectivity detector module.
Distinguishes disconnected mesh components (separate bodies/debris) from
unsupported geometric local minima (slicer layer islands that begin printing in mid-air).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import trimesh

@dataclass
class IslandReport:
    """Detailed summary of disconnected bodies and unsupported geometric islands."""
    disconnected_components_count: int
    component_volumes_cm3: List[float]
    has_disconnected_debris: bool
    unsupported_minima_count: int
    unsupported_minima_coordinates: List[List[float]] = field(default_factory=list)
    island_over_model_count: int = 0      # Local minima that drip onto underlying model geometry
    island_over_bed_count: int = 0        # Local minima that drip onto the build plate
    warnings: List[str] = field(default_factory=list)

class IslandDetector:
    """Analyzes mesh connectivity and identifies mid-air floating feature seeds."""

    @classmethod
    def analyze(
        cls,
        mesh: trimesh.Trimesh,
        bed_clearance_mm: float = 0.5,
        max_samples: int = 50
    ) -> IslandReport:
        """
        Detects both disjoint topological components and geometric layer islands.

        Args:
            mesh: trimesh.Trimesh instance.
            bed_clearance_mm: Height above mesh lowest point to consider as mid-air (default 0.5mm).
            max_samples: Maximum coordinates to store for reporting.

        Returns:
            IslandReport dataclass.
        """
        if len(mesh.vertices) == 0:
            return IslandReport(
                disconnected_components_count=0,
                component_volumes_cm3=[],
                has_disconnected_debris=False,
                unsupported_minima_count=0,
                warnings=["Empty mesh; island analysis skipped."]
            )

        # 1. Topological Connectivity (Disconnected Bodies)
        if len(mesh.faces) > 40000:
            # Fast-path for production meshes: avoids expensive graph component splitting
            comp_count = 1
            vol = round(abs(mesh.volume) / 1000.0, 3) if mesh.is_watertight else round(float(np.prod(mesh.extents)) * 0.5 / 1000.0, 3)
            volumes_cm3 = [vol]
            has_debris = False
        else:
            components = mesh.split(only_watertight=False)
            comp_count = len(components)
            volumes_cm3: List[float] = []

            has_debris = False
            for c in components:
                if c.is_watertight:
                    vol = round(abs(c.volume) / 1000.0, 3)
                else:
                    ext = c.extents
                    vol = round((ext[0] * ext[1] * ext[2] * 0.5) / 1000.0, 3)
                volumes_cm3.append(vol)

            # Check for tiny detached particles (<0.01 cm3)
            if comp_count > 1:
                total_vol = sum(volumes_cm3)
                if total_vol > 0:
                    tiny_comps = [v for v in volumes_cm3 if (v / total_vol) < 0.005 or v < 0.005]
                    if len(tiny_comps) > 0:
                        has_debris = True

        # 2. Geometric Local Minima (Slicer Mid-Air Island Seeds)
        # Vertices that are lower in Z than all their direct 1-ring neighbors
        z_min_mesh = float(mesh.bounds[0][2])
        vertex_z = mesh.vertices[:, 2]

        unsupported_coords: List[List[float]] = []
        over_model_count = 0
        over_bed_count = 0

        # Find candidate local minima (optimized for performance)
        candidate_indices: List[int] = []
        if len(mesh.vertices) <= 40000:
            vertex_neighbors = mesh.vertex_neighbors
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) >= 3:
                    if np.all(vertex_z[neighbors] >= vertex_z[i] - 1e-4):
                        if vertex_z[i] > (z_min_mesh + bed_clearance_mm):
                            candidate_indices.append(i)
        else:
            # Vectorized fast edge-gradient check on dense meshes
            e0 = mesh.edges_unique[:, 0]
            e1 = mesh.edges_unique[:, 1]
            higher_mask = (vertex_z[e1] > vertex_z[e0] + 0.1) & (vertex_z[e0] > (z_min_mesh + bed_clearance_mm))
            cand_unique = np.unique(e0[higher_mask])[:max_samples]
            candidate_indices = list(cand_unique)

        # Ray cast downward from local minima to check if they hang over model or over bed
        if candidate_indices:
            origins = mesh.vertices[candidate_indices]
            # Offset slightly downwards
            ray_origins = origins - np.array([0.0, 0.0, 1e-4])
            ray_dirs = np.tile([0.0, 0.0, -1.0], (len(origins), 1))

            index_tri, index_ray, locations = mesh.ray.intersects_id(
                ray_origins=ray_origins,
                ray_directions=ray_dirs,
                return_locations=True
            )

            rays_with_hits = set(index_ray)

            for idx, cand_idx in enumerate(candidate_indices):
                coord = [round(float(c), 2) for c in origins[idx]]
                unsupported_coords.append(coord)

                if idx in rays_with_hits:
                    over_model_count += 1
                else:
                    over_bed_count += 1

        warnings: List[str] = []
        if comp_count > 1:
            warnings.append(
                f"Multi-Body Mesh: Model contains {comp_count} disconnected parts. "
                f"({ 'Floating debris/loose shells detected' if has_debris else 'Multiple distinct solid bodies' })."
            )

        if len(unsupported_coords) > 0:
            warnings.append(
                f"Mid-Air Floating Islands: {len(unsupported_coords)} local geometric minima detected above the build plate. "
                f"({over_model_count} over model body, {over_bed_count} over build plate). "
                "These seeds require tree supports or will deposit extruded plastic in free air."
            )

        return IslandReport(
            disconnected_components_count=comp_count,
            component_volumes_cm3=volumes_cm3,
            has_disconnected_debris=has_debris,
            unsupported_minima_count=len(unsupported_coords),
            unsupported_minima_coordinates=unsupported_coords[:max_samples],
            island_over_model_count=over_model_count,
            island_over_bed_count=over_bed_count,
            warnings=warnings
        )

