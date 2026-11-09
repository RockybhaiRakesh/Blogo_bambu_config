"""
High-level Geometry Analyzer unifying loading, dimensional inspection, and validation.
"""

import os
import trimesh
from ..core.models import ModelInfo
from ..core.exceptions import GeometryLoadError
from .loader import load_mesh
from .dimensions import calculate_dimensions, check_build_volume_fit
from .mesh_validator import validate_mesh

class GeometryAnalyzer:
    """Orchestrates comprehensive 3D geometry analysis."""
    
    @classmethod
    def analyze_mesh(cls, mesh: trimesh.Trimesh, filepath: str = "") -> ModelInfo:
        """Analyzes an already-loaded in-memory mesh directly (zero disk latency)."""
        dims = calculate_dimensions(mesh)
        val = validate_mesh(mesh)
        fits, _ = check_build_volume_fit(dims["dim_x"], dims["dim_y"], dims["dim_z"])
        
        is_mini = bool(dims["dim_z"] < 65.0)
        
        return ModelInfo(
            filepath=filepath,
            filename=os.path.basename(filepath) if filepath else "mesh",
            vertices_count=val["vertices_count"],
            faces_count=val["faces_count"],
            dim_x=dims["dim_x"],
            dim_y=dims["dim_y"],
            dim_z=dims["dim_z"],
            is_watertight=val["is_watertight"],
            volume_cm3=val["volume_cm3"],
            fits_a1_bed=fits,
            aspect_ratio_z=dims["aspect_z"],
            is_miniature=is_mini
        )

    @classmethod
    def analyze(cls, filepath: str) -> ModelInfo:
        """Loads and analyzes a 3D model file, returning a structured ModelInfo record."""
        mesh = load_mesh(filepath)
        return cls.analyze_mesh(mesh, filepath)

