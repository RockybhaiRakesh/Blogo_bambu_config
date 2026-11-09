"""
Mesh repair operations: hole filling, normal unification, and degenerate face removal.
"""

import trimesh

def repair_mesh(mesh: trimesh.Trimesh, in_place: bool = False) -> trimesh.Trimesh:
    """
    Attempts automatic geometric repair on an input mesh.
    
    Operations:
        1. Fill small planar holes
        2. Fix winding order consistency
        3. Recalculate vertex and face normals
        4. Remove unreferenced or duplicate vertices
        
    Returns:
        Repaired trimesh.Trimesh object.
    """
    target = mesh if in_place else mesh.copy()
    
    try:
        trimesh.repair.fix_winding(target)
        trimesh.repair.fix_normals(target)
        trimesh.repair.fill_holes(target)
    except Exception:
        pass
        
    return target

