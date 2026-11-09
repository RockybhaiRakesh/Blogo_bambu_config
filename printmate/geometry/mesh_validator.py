"""
Mesh validation and geometric integrity inspection.
"""

from typing import Dict, Any
import trimesh

def validate_mesh(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """
    Performs comprehensive mesh integrity validation.
    
    Returns:
        Dict with keys:
            - is_watertight: bool
            - is_winding_consistent: bool
            - vertices_count: int
            - faces_count: int
            - naked_edges_count: int
            - volume_cm3: float
            - is_empty: bool
    """
    is_empty = len(mesh.vertices) == 0 or len(mesh.faces) == 0
    if is_empty:
        return {
            "is_watertight": False,
            "is_winding_consistent": False,
            "vertices_count": 0,
            "faces_count": 0,
            "naked_edges_count": 0,
            "volume_cm3": 0.0,
            "is_empty": True
        }
        
    is_watertight = bool(mesh.is_watertight)
    is_winding = bool(mesh.is_winding_consistent)
    
    # Calculate boundary (naked) edges
    try:
        naked_edges_count = len(trimesh.grouping.group_rows(mesh.edges_sorted, require_count=1))
    except Exception:
        naked_edges_count = 0
        
    # Calculate volume in cm3
    if is_watertight:
        vol_cm3 = float(round(abs(mesh.volume) / 1000.0, 2))
    else:
        # Approximate volume using bounding box * 0.5 packing factor
        extents = mesh.extents
        vol_cm3 = float(round((extents[0] * extents[1] * extents[2] * 0.5) / 1000.0, 2))
        
    return {
        "is_watertight": is_watertight,
        "is_winding_consistent": is_winding,
        "vertices_count": len(mesh.vertices),
        "faces_count": len(mesh.faces),
        "naked_edges_count": naked_edges_count,
        "volume_cm3": vol_cm3,
        "is_empty": False
    }

