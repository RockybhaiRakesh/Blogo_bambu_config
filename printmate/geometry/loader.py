"""
Safe 3D model mesh loader.
"""

import os
import trimesh
from ..core.exceptions import GeometryLoadError

SUPPORTED_EXTENSIONS = {".stl", ".obj", ".3mf", ".ply", ".off"}

def load_mesh(filepath: str, force_mesh: bool = True) -> trimesh.Trimesh:
    """
    Loads a 3D geometry file safely.
    
    Args:
        filepath: Path to geometry file.
        force_mesh: When True, ensures output is a single Trimesh object.
        
    Returns:
        trimesh.Trimesh object.
        
    Raises:
        GeometryLoadError: If file not found, unsupported format, or corrupt mesh.
    """
    if not os.path.exists(filepath):
        raise GeometryLoadError(f"Model file not found: {filepath}")
        
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise GeometryLoadError(f"Unsupported geometry extension '{ext}'. Supported: {SUPPORTED_EXTENSIONS}")
        
    try:
        loaded = trimesh.load(filepath, force="mesh" if force_mesh else None, process=False)
        if isinstance(loaded, trimesh.Scene):
            # Dump all geometries into a single mesh if a scene was returned
            if len(loaded.geometry) == 0:
                raise GeometryLoadError(f"Scene contains no mesh geometries: {filepath}")
            mesh = trimesh.util.concatenate([geom for geom in loaded.geometry.values() if isinstance(geom, trimesh.Trimesh)])
            return mesh
        elif isinstance(loaded, trimesh.Trimesh):
            return loaded
        else:
            raise GeometryLoadError(f"Unexpected loaded object type: {type(loaded)}")
    except Exception as e:
        if isinstance(e, GeometryLoadError):
            raise
        raise GeometryLoadError(f"Failed to load mesh from '{filepath}': {str(e)}") from e

