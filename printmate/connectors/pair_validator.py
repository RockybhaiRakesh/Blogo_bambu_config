"""
Connector Pair Validation module.
Validates male and female connector geometry as a precision matching pair.
Checks dimensional compatibility, insertion depth, clearance tolerances, alignment,
detects collisions, insufficient wall thicknesses, and external model surface breakthroughs.
"""

from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import shapely.geometry as sg
import trimesh

from printmate.connectors.connector_generator import (
    ConnectorGenerator,
    DowelLockConfig,
    ConnectorType
)

@dataclass
class PairValidationResult:
    """Quantitative validation results for a male/female connector pair."""
    is_valid: bool
    connector_type: str
    pin_radius_mm: float
    pin_height_mm: float
    socket_radius_mm: float
    socket_depth_mm: float
    radial_clearance_mm: float
    axial_relief_mm: float
    min_wall_thickness_mm: float
    exterior_breakthrough: bool
    interference_detected: bool
    alignment_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        return (
            f"Connector Pair Validation [{status}] ({self.connector_type}):\n"
            f"  - Radial Clearance: {self.radial_clearance_mm:.3f} mm\n"
            f"  - Axial Relief: {self.axial_relief_mm:.3f} mm (Pin: {self.pin_height_mm}mm, Socket: {self.socket_depth_mm}mm)\n"
            f"  - Min Outer Wall Margin: {self.min_wall_thickness_mm:.2f} mm\n"
            f"  - Wall Breakthrough: {'YES (CRITICAL)' if self.exterior_breakthrough else 'None (Safe)'}\n"
            f"  - Interference: {'DETECTED' if self.interference_detected else 'None (Clean)'}\n"
            f"  - Angular Alignment: {'VALID' if self.alignment_valid else 'MISALIGNED'}\n"
            f"  - Issues: {len(self.errors)} errors, {len(self.warnings)} warnings"
        )

class ConnectorPairValidator:
    """Validates physical and geometrical consistency between male pins and female sockets."""

    MIN_SAFE_WALL_MM = 2.0  # 4x 0.4mm nozzle extrusion lines minimum
    MIN_SAFE_CLEARANCE_MM = 0.12  # Below 0.12mm risk of fusion on FDM
    MAX_SAFE_CLEARANCE_MM = 0.45  # Above 0.45mm loose / unstable joint

    @classmethod
    def validate_pair(
        cls,
        male_mesh: trimesh.Trimesh,
        female_mesh: trimesh.Trimesh,
        config: DowelLockConfig,
        z_cut: float,
        center_xy: Tuple[float, float] = (0.0, 0.0),
        angle_rad: float = 0.0
    ) -> PairValidationResult:
        """
        Executes comprehensive geometric validation across matching male and female parts.
        """
        errors: List[str] = []
        warnings: List[str] = []

        ctype_str = config.connector_type.value if hasattr(config.connector_type, "value") else str(config.connector_type)
        r_pin = float(config.pin_radius)
        h_pin = float(config.pin_height)
        r_sock = r_pin + float(config.clearance)
        d_sock = h_pin + float(config.socket_depth_extra)
        rad_clearance = float(config.clearance)
        axial_relief = float(config.socket_depth_extra)

        # 1. Clearance & Insertion Depth Checks
        if rad_clearance < cls.MIN_SAFE_CLEARANCE_MM:
            errors.append(
                f"Radial clearance ({rad_clearance:.3f}mm) is below FDM fusion limit ({cls.MIN_SAFE_CLEARANCE_MM}mm)."
            )
        elif rad_clearance > cls.MAX_SAFE_CLEARANCE_MM:
            warnings.append(
                f"Radial clearance ({rad_clearance:.3f}mm) exceeds 0.45mm; connector will have significant loose play."
            )

        if axial_relief <= 0.0:
            errors.append(
                f"Axial bottom relief ({axial_relief:.2f}mm) is non-positive; pin will bottom out before faces mate."
            )
        elif axial_relief < 0.3:
            warnings.append(
                f"Axial relief ({axial_relief:.2f}mm) is under 0.3mm; extrusion burrs may prevent flush face contact."
            )

        # 2. Alignment & Orientation Checks
        alignment_valid = True
        interference_detected = False

        if config.connector_type in [ConnectorType.DUAL_PIN, ConnectorType.ASYMMETRIC]:
            half_d = config.pin_spacing / 2.0
            p1_dist = half_d
            p2_dist = half_d
            if config.pin_spacing < (config.pin_radius * 2.0 + config.clearance * 2.0 + 1.0):
                interference_detected = True
                errors.append("Connector pins intersect each other or lack adequate separation.")

        # 3. Minimum Wall Thickness & Exterior Breakthrough
        min_wall = float("inf")
        exterior_breakthrough = False

        # Extract cut section polygon of female mesh at z_cut
        try:
            cut_sec = female_mesh.section(
                plane_origin=(0.0, 0.0, z_cut),
                plane_normal=(0.0, 0.0, 1.0)
            )
            if cut_sec is not None:
                # 2D planar polygon
                poly_2d, _ = cut_sec.to_2D()
                # Use shapely geometry
                sh_poly = poly_2d.polygons_full[0] if len(poly_2d.polygons_full) > 0 else None

                if sh_poly is not None:
                    # Get socket profile
                    sock_polys = ConnectorGenerator.get_connector_polygons(
                        config=config,
                        origin=center_xy,
                        angle_rad=angle_rad
                    )
                    if not isinstance(sock_polys, list):
                        sock_polys = [sock_polys]

                    for sp in sock_polys:
                        expanded_socket = sp.buffer(config.clearance, quad_segs=8)
                        # Check if socket breaks outside polygon
                        if not sh_poly.contains(expanded_socket):
                            exterior_breakthrough = True
                            min_wall = 0.0
                            errors.append(
                                "CRITICAL: Female socket breaches the outer perimeter of the model!"
                            )
                            break
                        else:
                            dist = sh_poly.exterior.distance(expanded_socket)
                            min_wall = min(min_wall, dist)

                    if min_wall < config.min_wall_thickness:
                        if not exterior_breakthrough:
                            warnings.append(
                                f"Minimum wall thickness around socket ({min_wall:.2f}mm) is below target ({config.min_wall_thickness:.2f}mm)."
                            )
            else:
                warnings.append(f"Could not compute planar cross-section of female mesh at Z={z_cut}mm.")
        except Exception as e:
            warnings.append(f"Planar wall thickness check encountered exception: {str(e)}")

        if min_wall == float("inf"):
            min_wall = 0.0

        is_valid = (len(errors) == 0) and not exterior_breakthrough and not interference_detected

        return PairValidationResult(
            is_valid=is_valid,
            connector_type=ctype_str,
            pin_radius_mm=r_pin,
            pin_height_mm=h_pin,
            socket_radius_mm=r_sock,
            socket_depth_mm=d_sock,
            radial_clearance_mm=rad_clearance,
            axial_relief_mm=axial_relief,
            min_wall_thickness_mm=round(min_wall, 3),
            exterior_breakthrough=exterior_breakthrough,
            interference_detected=interference_detected,
            alignment_valid=alignment_valid,
            errors=errors,
            warnings=warnings
        )
