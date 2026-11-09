"""
3D Model dimension calculations and build plate fit testing.
"""

from typing import Tuple, Dict
import numpy as np
import trimesh
from ..core.config import Config

def calculate_dimensions(mesh: trimesh.Trimesh) -> Dict[str, float]:
    """
    Computes exact dimensions, bounding box, and aspect ratios.
    
    Returns:
        Dict with keys: dim_x, dim_y, dim_z, min_x, max_x, min_y, max_y, min_z, max_z, aspect_z
    """
    bounds = mesh.bounds
    extents = mesh.extents
    
    min_pt = bounds[0]
    max_pt = bounds[1]
    
    dim_x = float(round(extents[0], 2))
    dim_y = float(round(extents[1], 2))
    dim_z = float(round(extents[2], 2))
    
    # Calculate aspect ratio (height relative to average base width)
    base_dim = max(0.1, (dim_x + dim_y) / 2.0)
    aspect_z = float(round(dim_z / base_dim, 2))
    
    return {
        "dim_x": dim_x,
        "dim_y": dim_y,
        "dim_z": dim_z,
        "min_x": float(round(min_pt[0], 2)),
        "max_x": float(round(max_pt[0], 2)),
        "min_y": float(round(min_pt[1], 2)),
        "max_y": float(round(max_pt[1], 2)),
        "min_z": float(round(min_pt[2], 2)),
        "max_z": float(round(max_pt[2], 2)),
        "aspect_z": aspect_z
    }

def check_build_volume_fit(dim_x: float, dim_y: float, dim_z: float) -> Tuple[bool, str]:
    """
    Checks if model dimensions fit within target printer build volume (Bambu Lab A1: 256x256x256mm).
    """
    hw = Config.hardware
    fits_x = dim_x <= hw.build_volume_x
    fits_y = dim_y <= hw.build_volume_y
    fits_z = dim_z <= hw.build_volume_z
    
    if fits_x and fits_y and fits_z:
        return True, "Fits within build volume."
        
    exceeded = []
    if not fits_x: exceeded.append(f"X ({dim_x} > {hw.build_volume_x}mm)")
    if not fits_y: exceeded.append(f"Y ({dim_y} > {hw.build_volume_y}mm)")
    if not fits_z: exceeded.append(f"Z ({dim_z} > {hw.build_volume_z}mm)")
    
    return False, f"Model exceeds build volume in: {', '.join(exceeded)}"

