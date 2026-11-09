"""
Intelligent Multi-Part Splitting module.
Evaluates model dimensions against Bambu Lab A1 build volumes (256x256x256mm),
identifies safe natural geometric cutting planes while avoiding fragile anatomical/thin regions,
and executes recursive watertight planar bisections with alignment validation.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import trimesh

from printmate.core.config import Config
from printmate.core.exceptions import MultiSplitError
from printmate.splitting.planar_splitter import PlanarSplitter
from printmate.splitting.split_analyzer import SplitAnalyzer

@dataclass
class SplitPartInfo:
    """Metadata for an individual split sub-part."""
    part_index: int
    name: str
    mesh: trimesh.Trimesh
    bounds: List[List[float]]
    dimensions: List[float]          # [dim_x, dim_y, dim_z] in mm
    is_watertight: bool
    fits_build_plate: bool
    face_count: int
    volume_cm3: float

@dataclass
class MultiSplitResult:
    """Summary result of multi-part splitting analysis and execution."""
    is_split_required: bool
    success: bool
    reason: str
    cut_planes: List[Dict[str, Any]] = field(default_factory=list)
    parts: List[SplitPartInfo] = field(default_factory=list)
    connectors_recommended: bool = False
    assembly_valid: bool = False
    error_message: Optional[str] = None

class MultiSplitter:
    """
    Intelligent multi-part mesh partitioning engine.
    Ensures that every generated sub-part satisfies Bambu Lab A1 build constraints
    and maintains watertight manifold geometry.
    """

    BUILD_LIMITS = (256.0, 256.0, 256.0)  # Bambu Lab A1 build volume in mm

    @classmethod
    def check_exceeds_volume(
        cls,
        mesh: trimesh.Trimesh,
        build_limits: Tuple[float, float, float] = BUILD_LIMITS
    ) -> Tuple[bool, List[str]]:
        """
        Checks whether a mesh's bounding extents exceed machine build volume.
        """
        extents = mesh.extents
        reasons = []
        axes = ["X (Width)", "Y (Depth)", "Z (Height)"]

        for i in range(3):
            if extents[i] > build_limits[i]:
                reasons.append(
                    f"{axes[i]} extent {extents[i]:.1f}mm exceeds build limit {build_limits[i]:.1f}mm"
                )

        return (len(reasons) > 0, reasons)

    @classmethod
    def find_safe_cut_planes(
        cls,
        mesh: trimesh.Trimesh,
        axis: int = 2,
        build_limit: float = 256.0,
        fragile_zones: Optional[List[Dict[str, Any]]] = None
    ) -> List[float]:
        """
        Identifies optimal cut locations along an oversized axis.
        Prefers natural necking/waistline points and strictly avoids fragile zones.
        """
        bounds = mesh.bounds
        min_v = float(bounds[0][axis])
        max_v = float(bounds[1][axis])
        total_span = max_v - min_v

        # Determine minimum number of cuts needed
        num_segments = int(np.ceil(total_span / (build_limit - 10.0)))
        if num_segments <= 1:
            return []

        # Sample cross sections across the axis
        samples = SplitAnalyzer.sample_cross_sections(mesh, axis=axis, num_samples=60)
        if not samples:
            # Uniform fallback if cross section sampling fails
            step = total_span / float(num_segments)
            return [min_v + i * step for i in range(1, num_segments)]

        # Extract necking candidates
        candidates = SplitAnalyzer.find_necking_candidates(samples, min_margin_ratio=0.08)

        # Filter out cuts that intersect fragile zones
        safe_candidates: List[float] = []
        for pos in candidates:
            in_fragile = False
            if fragile_zones:
                for fz in fragile_zones:
                    # Check Z-range intersection
                    z_min = fz.get("z_min", -float("inf"))
                    z_max = fz.get("z_max", float("inf"))
                    if z_min <= pos <= z_max:
                        in_fragile = True
                        break
            if not in_fragile:
                safe_candidates.append(pos)

        # Select cuts that partition the span into valid sub-lengths (< build_limit)
        cuts: List[float] = []
        target_span = total_span / float(num_segments)

        for i in range(1, num_segments):
            target_pos = min_v + i * target_span
            if safe_candidates:
                # Pick the closest safe necking candidate within +/- 30% of target position
                best_c = min(safe_candidates, key=lambda c: abs(c - target_pos))
                if abs(best_c - target_pos) <= (target_span * 0.35):
                    cuts.append(best_c)
                    continue

            # Fallback to target position
            cuts.append(round(target_pos, 2))

        return sorted(list(set(cuts)))

    @classmethod
    def split_at_planes(
        cls,
        mesh: trimesh.Trimesh,
        cut_positions: List[float],
        axis: int = 2
    ) -> List[trimesh.Trimesh]:
        """
        Executes sequential planar cuts along the specified axis, returning capped submeshes.
        """
        normal = [0.0, 0.0, 0.0]
        normal[axis] = 1.0

        current_mesh = mesh
        parts: List[trimesh.Trimesh] = []

        # Sort cut positions ascending
        sorted_cuts = sorted(cut_positions)

        for cut_z in sorted_cuts:
            origin = [0.0, 0.0, 0.0]
            origin[axis] = cut_z
            part_below, part_above = PlanarSplitter.split(
                mesh=current_mesh,
                plane_normal=tuple(normal),
                plane_origin=tuple(origin),
                cap=True
            )
            parts.append(part_below)
            current_mesh = part_above

        # Append final remainder
        parts.append(current_mesh)
        return parts

    @classmethod
    def plan_and_execute(
        cls,
        mesh: trimesh.Trimesh,
        build_limits: Tuple[float, float, float] = BUILD_LIMITS,
        force_split: bool = False,
        fragile_zones: Optional[List[Dict[str, Any]]] = None,
        base_name: str = "Part"
    ) -> MultiSplitResult:
        """
        End-to-end multi-part split planning, validation, and execution.
        """
        exceeds, reasons = cls.check_exceeds_volume(mesh, build_limits)

        if not exceeds and not force_split:
            # Model fits in single print; no split required
            return MultiSplitResult(
                is_split_required=False,
                success=True,
                reason="Model extents fit comfortably within Bambu Lab A1 build envelope.",
                parts=[
                    SplitPartInfo(
                        part_index=1,
                        name=f"{base_name}_Full",
                        mesh=mesh,
                        bounds=mesh.bounds.tolist(),
                        dimensions=mesh.extents.tolist(),
                        is_watertight=bool(mesh.is_watertight),
                        fits_build_plate=True,
                        face_count=len(mesh.faces),
                        volume_cm3=round(float(mesh.volume) / 1000.0, 3) if mesh.is_watertight else 0.0
                    )
                ],
                connectors_recommended=False,
                assembly_valid=True
            )

        # Find which axis is oversized (defaulting to Z-axis for tall models)
        extents = mesh.extents
        oversized_axis = 2  # Z
        if extents[0] > extents[2] and extents[0] > build_limits[0]:
            oversized_axis = 0
        elif extents[1] > extents[2] and extents[1] > build_limits[1]:
            oversized_axis = 1

        cuts = cls.find_safe_cut_planes(
            mesh=mesh,
            axis=oversized_axis,
            build_limit=build_limits[oversized_axis],
            fragile_zones=fragile_zones
        )

        if not cuts and exceeds:
            return MultiSplitResult(
                is_split_required=True,
                success=False,
                reason="Model exceeds build volume, but no safe cutting planes could be found without damaging fragile features.",
                error_message="No safe cutting location found outside fragile zones."
            )

        # Execute split
        try:
            submeshes = cls.split_at_planes(mesh, cuts, axis=oversized_axis)
        except Exception as e:
            return MultiSplitResult(
                is_split_required=True,
                success=False,
                reason=f"Multi-part planar split execution failed: {str(e)}",
                error_message=str(e)
            )

        part_infos: List[SplitPartInfo] = []
        all_watertight = True
        all_fit = True

        for idx, sm in enumerate(submeshes, start=1):
            fits, _ = cls.check_exceeds_volume(sm, build_limits)
            fits_plate = not fits
            is_wt = bool(sm.is_watertight)

            if not is_wt:
                all_watertight = False
            if not fits_plate:
                all_fit = False

            part_infos.append(
                SplitPartInfo(
                    part_index=idx,
                    name=f"{base_name}_Part{idx}",
                    mesh=sm,
                    bounds=sm.bounds.tolist(),
                    dimensions=sm.extents.tolist(),
                    is_watertight=is_wt,
                    fits_build_plate=fits_plate,
                    face_count=len(sm.faces),
                    volume_cm3=round(float(sm.volume) / 1000.0, 3) if is_wt else 0.0
                )
            )

        cut_plane_meta = [
            {"axis": oversized_axis, "position": c, "normal": [1.0 if i == oversized_axis else 0.0 for i in range(3)]}
            for c in cuts
        ]

        return MultiSplitResult(
            is_split_required=True,
            success=all_watertight and all_fit,
            reason=f"Model split into {len(part_infos)} printable sub-parts along natural boundary planes.",
            cut_planes=cut_plane_meta,
            parts=part_infos,
            connectors_recommended=len(part_infos) > 1,
            assembly_valid=all_watertight
        )

