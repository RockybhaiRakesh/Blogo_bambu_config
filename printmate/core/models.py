"""
Domain data models for PRINTMATE AI.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class ModelInfo:
    filepath: str
    filename: str
    vertices_count: int
    faces_count: int
    dim_x: float
    dim_y: float
    dim_z: float
    is_watertight: bool
    volume_cm3: float
    fits_a1_bed: bool = True
    aspect_ratio_z: float = 1.0
    is_miniature: bool = False

    @property
    def file(self) -> str:
        return self.filepath

    @property
    def vertices(self) -> int:
        return self.vertices_count

    @property
    def faces(self) -> int:
        return self.faces_count

@dataclass
class SlicerProfile:
    nozzle_diameter: float = 0.4
    layer_height: float = 0.12
    wall_loops: int = 3
    infill_pattern: str = "gyroid"
    infill_density: str = "15%"
    enable_support: bool = True
    support_type: str = "tree(auto)"
    support_style: str = "tree_slim"
    top_z_distance: float = 0.24
    object_xy_distance: float = 0.60
    brim_type: str = "outer_only"
    brim_width: float = 5.0
    outer_wall_speed: float = 55.0
    inner_wall_speed: float = 120.0
    wall_generator: str = "arachne"
    seam_position: str = "back"

@dataclass
class PrintStrategy:
    mode: str = "single"  # 'single' or 'split'
    filament: str = "pla_basic"
    target_height_mm: Optional[float] = None
    profile: SlicerProfile = field(default_factory=SlicerProfile)

@dataclass
class WorkflowResult:
    success: bool
    message: str = ""
    model_info: Optional[ModelInfo] = None
    generated_3mf_path: Optional[str] = None
    output_file: Optional[str] = None
    split_parts: List[str] = field(default_factory=list)
    slicer_launched: bool = False
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.output_file and not self.generated_3mf_path:
            self.generated_3mf_path = self.output_file
        elif self.generated_3mf_path and not self.output_file:
            self.output_file = self.generated_3mf_path
