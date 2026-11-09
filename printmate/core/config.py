"""
Centralized Configuration for PRINTMATE AI.
"""

import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class HardwareConfig:
    printer_name: str = "Bambu Lab A1"
    nozzle_diameter: float = 0.4
    build_volume_x: float = 256.0
    build_volume_y: float = 256.0
    build_volume_z: float = 256.0
    default_plate_type: str = "Textured PEI Plate"

@dataclass
class SafeSupportConfig:
    support_type: str = "tree(auto)"
    support_style: str = "tree_slim"
    top_z_distance: float = 0.24         # Verified safe gap preventing hand welding
    object_xy_distance: float = 0.60     # Verified clearance preventing side hugging
    threshold_angle: int = 30
    interface_top_layers: int = 2

@dataclass
class SafeQualityConfig:
    layer_height: float = 0.12
    wall_loops: int = 3
    sparse_infill_pattern: str = "gyroid"
    sparse_infill_density: str = "15%"
    brim_type: str = "outer_only"
    brim_width: float = 5.0
    seam_position: str = "back"
    wall_generator: str = "arachne"

@dataclass
class Settings:
    workspace_dir: str = r"c:\Users\rakes\OneDrive\Desktop\3dMOdel_agent"
    bambu_studio_exe: str = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
    blender_exe: str = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
    golden_template_3mf: str = r"C:\Users\rakes\Downloads\single_color.3mf"
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    support: SafeSupportConfig = field(default_factory=SafeSupportConfig)
    quality: SafeQualityConfig = field(default_factory=SafeQualityConfig)

    # Backward-compatible uppercase aliases
    @property
    def WORKSPACE_DIR(self) -> str:
        return self.workspace_dir

    @property
    def BAMBU_STUDIO_EXE(self) -> str:
        return self.bambu_studio_exe

    @property
    def BLENDER_EXE(self) -> str:
        return self.blender_exe

    @property
    def GOLDEN_TEMPLATE_3MF(self) -> str:
        local_tpl = os.path.join(self.workspace_dir, "printmate", "templates", "golden_bambu_a1.3mf")
        if os.path.exists(local_tpl):
            return local_tpl
        return self.golden_template_3mf

Config = Settings()
