"""
Assembly Simulation and Reconstruction module.
Simulates physical assembly of 3D printed split sub-parts.
Verifies spatial alignment, detects gaps and overlapping interference,
measures bounding box fidelity against the original model, and ensures part completeness.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import trimesh

@dataclass
class AssemblyValidationReport:
    """Detailed validation metrics from simulated assembly reconstruction."""
    is_valid: bool
    assembled_parts_count: int
    expected_parts_count: int
    bounds_max_delta_mm: float
    volume_delta_pct: float
    gaps_detected: bool
    max_gap_mm: float
    overlaps_detected: bool
    max_overlap_mm: float
    original_bounds: List[List[float]] = field(default_factory=list)
    assembled_bounds: List[List[float]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Assembly Simulation [{status}]: {self.assembled_parts_count}/{self.expected_parts_count} parts assembled\n"
            f"  - Bounding Box Fidelity: Max Delta = {self.bounds_max_delta_mm:.4f} mm\n"
            f"  - Volume Deviation: {self.volume_delta_pct:.2f}%\n"
            f"  - Gaps Between Parts: {'DETECTED (' + str(self.max_gap_mm) + 'mm)' if self.gaps_detected else 'None (Flush)'}\n"
            f"  - Overlaps / Collisions: {'DETECTED (' + str(self.max_overlap_mm) + 'mm)' if self.overlaps_detected else 'None (Clean)'}\n"
            f"  - Issues: {len(self.errors)} errors, {len(self.warnings)} warnings"
        )

class AssemblySimulator:
    """Simulates virtual re-assembly and validates topological and spatial continuity."""

    MAX_TOLERABLE_GAP_MM = 0.20       # Gaps greater than 0.20mm indicate parting error
    MAX_TOLERABLE_OVERLAP_MM = 0.15   # Overlaps greater than 0.15mm indicate intersection error
    MAX_BOUNDS_DEVIATION_MM = 0.25    # Bounding box expansion limit

    @classmethod
    def simulate_assembly(
        cls,
        parts: List[Union[str, trimesh.Trimesh]],
        original_mesh: Optional[Union[str, trimesh.Trimesh]] = None,
        expected_part_count: Optional[int] = None,
        pin_height_offset: float = 0.0
    ) -> AssemblyValidationReport:
        """
        Reconstructs the full assembly from split parts and evaluates geometric continuity.
        """
        errors: List[str] = []
        warnings: List[str] = []

        loaded_parts: List[trimesh.Trimesh] = []
        for p in parts:
            if isinstance(p, str):
                if not os.path.exists(p):
                    errors.append(f"Missing split part file: {p}")
                    continue
                loaded_parts.append(trimesh.load(p, process=False))
            elif isinstance(p, trimesh.Trimesh):
                loaded_parts.append(p)

        n_parts = len(loaded_parts)
        exp_count = expected_part_count or n_parts

        # 1. Part Count & Completeness
        if n_parts != exp_count:
            errors.append(f"Part count mismatch: expected {exp_count} parts, but found {n_parts}.")

        if n_parts == 0:
            return AssemblyValidationReport(
                is_valid=False,
                assembled_parts_count=0,
                expected_parts_count=exp_count,
                bounds_max_delta_mm=0.0,
                volume_delta_pct=100.0,
                gaps_detected=False,
                max_gap_mm=0.0,
                overlaps_detected=False,
                max_overlap_mm=0.0,
                errors=errors
            )

        # 2. Check each part's manifoldness
        for idx, lp in enumerate(loaded_parts, start=1):
            if not lp.is_watertight:
                warnings.append(f"Part {idx} is not watertight / has open boundary edges.")

        # 3. Sort parts vertically along Z axis
        sorted_parts = sorted(loaded_parts, key=lambda m: m.bounds[0][2])

        # 4. Measure interfacial gaps and overlaps
        max_gap = 0.0
        max_overlap = 0.0
        gaps_detected = False
        overlaps_detected = False

        for i in range(len(sorted_parts) - 1):
            lower_top_z = float(sorted_parts[i].bounds[1][2]) - pin_height_offset
            upper_bot_z = float(sorted_parts[i + 1].bounds[0][2])

            diff = upper_bot_z - lower_top_z

            if diff > cls.MAX_TOLERABLE_GAP_MM:
                gaps_detected = True
                max_gap = max(max_gap, diff)
                warnings.append(
                    f"Interfacial gap of {diff:.3f}mm detected between Part {i+1} and Part {i+2}."
                )
            elif diff < -cls.MAX_TOLERABLE_OVERLAP_MM:
                overlaps_detected = True
                overlap_val = abs(diff)
                max_overlap = max(max_overlap, overlap_val)
                warnings.append(
                    f"Interfacial overlap of {overlap_val:.3f}mm detected between Part {i+1} and Part {i+2}."
                )

        # 5. Combined Bounding Box & Volume Comparison
        combined_mesh = trimesh.util.concatenate(sorted_parts)
        assembled_bounds = combined_mesh.bounds.tolist()
        assembled_vol = float(combined_mesh.volume) if combined_mesh.is_watertight else 0.0

        orig_bounds: List[List[float]] = []
        bounds_delta = 0.0
        vol_delta_pct = 0.0

        if original_mesh is not None:
            if isinstance(original_mesh, str):
                orig_m = trimesh.load(original_mesh, process=False)
            else:
                orig_m = original_mesh

            orig_bounds = orig_m.bounds.tolist()
            b_orig = np.array(orig_bounds)
            b_asmb = np.array(assembled_bounds)

            # Max deviation across min/max coordinates
            bounds_delta = float(np.max(np.abs(b_orig - b_asmb)))
            if bounds_delta > cls.MAX_BOUNDS_DEVIATION_MM:
                errors.append(
                    f"Assembled bounding box deviates by {bounds_delta:.3f}mm from original model (limit: {cls.MAX_BOUNDS_DEVIATION_MM}mm)."
                )

            if orig_m.is_watertight and assembled_vol > 0.0:
                orig_vol = float(orig_m.volume)
                vol_delta_pct = (abs(orig_vol - assembled_vol) / orig_vol) * 100.0
                if vol_delta_pct > 3.0:
                    warnings.append(
                        f"Assembled volume deviation ({vol_delta_pct:.2f}%) exceeds 3.0% threshold."
                    )
        else:
            orig_bounds = assembled_bounds

        is_valid = len(errors) == 0

        return AssemblyValidationReport(
            is_valid=is_valid,
            assembled_parts_count=n_parts,
            expected_parts_count=exp_count,
            bounds_max_delta_mm=round(bounds_delta, 4),
            volume_delta_pct=round(vol_delta_pct, 3),
            gaps_detected=gaps_detected,
            max_gap_mm=round(max_gap, 4),
            overlaps_detected=overlaps_detected,
            max_overlap_mm=round(max_overlap, 4),
            original_bounds=orig_bounds,
            assembled_bounds=assembled_bounds,
            errors=errors,
            warnings=warnings
        )
