"""
Planar mesh splitting module.
Bisects a 3D mesh across an arbitrary cutting plane with automatic cap triangulation.
"""

from typing import Tuple
import trimesh
from printmate.core.exceptions import SplitError

class PlanarSplitter:
    """Executes watertight planar cuts through 3D meshes."""

    @staticmethod
    def split(
        mesh: trimesh.Trimesh,
        plane_normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        plane_origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        cap: bool = True
    ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """
        Splits a mesh into two separate watertight meshes using a plane.

        Args:
            mesh: trimesh.Trimesh instance.
            plane_normal: Normal vector of the slicing plane.
            plane_origin: Point lying on the slicing plane.
            cap: Whether to cap open cross-sectional boundaries.

        Returns:
            Tuple of (part_below, part_above) meshes.
        """
        if not isinstance(mesh, trimesh.Trimesh):
            raise SplitError("Input must be a valid trimesh.Trimesh instance.")

        try:
            # Positive normal direction
            part_above = mesh.slice_plane(
                plane_origin=plane_origin,
                plane_normal=plane_normal,
                cap=cap
            )

            # Inverted normal direction for the other half
            neg_normal = tuple(-x for x in plane_normal)
            part_below = mesh.slice_plane(
                plane_origin=plane_origin,
                plane_normal=neg_normal,
                cap=cap
            )

            if len(part_above.faces) == 0 or len(part_below.faces) == 0:
                raise SplitError(
                    f"Plane at {plane_origin} with normal {plane_normal} does not intersect the mesh interior."
                )

            return part_below, part_above

        except Exception as e:
            if isinstance(e, SplitError):
                raise
            raise SplitError(f"Mesh planar split failed: {str(e)}") from e

    @classmethod
    def split_and_cap(
        cls,
        mesh: trimesh.Trimesh,
        plane_normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        plane_origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> Tuple[trimesh.Trimesh, trimesh.Trimesh]:
        """Convenience alias for split with cap=True."""
        return cls.split(
            mesh=mesh,
            plane_normal=plane_normal,
            plane_origin=plane_origin,
            cap=True
        )

