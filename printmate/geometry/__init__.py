"""
Geometry processing modules: loading, dimensional calculation, validation, repair,
wall thickness analysis, overhang analysis, and floating island detection.
"""

from .loader import load_mesh
from .dimensions import calculate_dimensions, check_build_volume_fit
from .mesh_validator import validate_mesh
from .mesh_repair import repair_mesh
from .analyzer import GeometryAnalyzer
from .thickness_analyzer import ThicknessAnalyzer, ThicknessReport
from .overhang_analyzer import OverhangAnalyzer, OverhangReport
from .island_detector import IslandDetector, IslandReport

__all__ = [
    "load_mesh",
    "calculate_dimensions",
    "check_build_volume_fit",
    "validate_mesh",
    "repair_mesh",
    "GeometryAnalyzer",
    "ThicknessAnalyzer",
    "ThicknessReport",
    "OverhangAnalyzer",
    "OverhangReport",
    "IslandDetector",
    "IslandReport",
]
