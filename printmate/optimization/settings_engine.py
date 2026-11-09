"""
Intelligent Print Settings Optimization Engine.
Synthesizes geometric intelligence, material thermal properties, machine kinematic constraints,
and selectable print objectives into optimal production slicer profiles.
Provides transparent engineering rationales for all recommended parameters.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import trimesh

from printmate.profiles.printer_profiles import PrinterProfile, PrinterProfileRegistry
from printmate.profiles.filament_profiles import FilamentProfile, FilamentProfileRegistry
from printmate.optimization.settings_validator import SettingsValidator, CompatibilityResult

class OptimizationObjective(str, Enum):
    """Target engineering objective for print preparation."""
    FINE_DETAIL = "fine_detail"              # High surface resolution, delicate figurines (0.08-0.12mm)
    BALANCED_QUALITY = "balanced_quality"    # Production general-purpose balance (0.16-0.20mm)
    STRONG_FUNCTIONAL = "strong_functional"  # Maximum tensile, shear, and connector strength (4-5 walls)
    FAST_PRINTING = "fast_printing"          # Rapid draft and prototyping (0.24-0.28mm, high flow)
    MINIMUM_MATERIAL = "minimum_material"    # Lightweight, low plastic consumption (sparse infill)
    SUPPORT_MINIMIZED = "support_minimized"  # Steep threshold angle, tree slim supports, zero scarring

@dataclass
class OptimizedSettings:
    """Comprehensive, validated print process configuration with engineering rationales."""
    objective: OptimizationObjective
    printer: PrinterProfile
    filament: FilamentProfile
    layer_height: float
    initial_layer_height: float
    wall_loops: int
    top_shell_layers: int
    bottom_shell_layers: int
    sparse_infill_density: str
    sparse_infill_pattern: str
    nozzle_temperature: float
    bed_temperature: float
    outer_wall_speed_mm_s: float
    inner_wall_speed_mm_s: float
    sparse_infill_speed_mm_s: float
    enable_support: bool
    support_type: str
    support_style: str
    support_top_z_distance: float
    support_object_xy_distance: float
    support_threshold_angle: int
    brim_type: str
    brim_width_mm: float
    wall_generator: str = "arachne"
    seam_position: str = "back"
    compatibility: Optional[CompatibilityResult] = None
    reasoning: Dict[str, str] = field(default_factory=dict)
    estimated_filament_grams: float = 0.0
    estimated_print_time_mins: float = 0.0

    def to_slicer_overrides(self) -> Dict[str, Any]:
        """Converts settings to Bambu Studio project_settings.config JSON key-values."""
        return {
            "printer_model": self.printer.name,
            "nozzle_diameter": [str(self.printer.default_nozzle_diameter)],
            "layer_height": f"{self.layer_height:.2f}",
            "initial_layer_print_height": f"{self.initial_layer_height:.2f}",
            "wall_loops": str(self.wall_loops),
            "top_shell_layers": str(self.top_shell_layers),
            "bottom_shell_layers": str(self.bottom_shell_layers),
            "sparse_infill_pattern": self.sparse_infill_pattern,
            "sparse_infill_density": self.sparse_infill_density,
            "nozzle_temperature": [str(int(self.nozzle_temperature))],
            "nozzle_temperature_initial_layer": [str(int(self.nozzle_temperature + 5))],
            "hot_plate_temp": [str(int(self.bed_temperature))],
            "outer_wall_speed": [str(int(self.outer_wall_speed_mm_s))],
            "inner_wall_speed": [str(int(self.inner_wall_speed_mm_s))],
            "sparse_infill_speed": [str(int(self.sparse_infill_speed_mm_s))],
            "enable_support": "1" if self.enable_support else "0",
            "support_type": self.support_type,
            "support_style": self.support_style,
            "support_top_z_distance": f"{self.support_top_z_distance:.2f}",
            "support_object_xy_distance": f"{self.support_object_xy_distance:.2f}",
            "support_threshold_angle": str(self.support_threshold_angle),
            "brim_type": self.brim_type,
            "brim_width": str(int(self.brim_width_mm)),
            "wall_generator": self.wall_generator,
            "seam_position": self.seam_position,
        }

    def summary(self) -> str:
        return (
            f"OptimizedSettings [{self.objective.value.upper()} | {self.printer.name} | {self.filament.brand} {self.filament.material_name}]:\n"
            f"  - Layer Height: {self.layer_height:.2f}mm (Initial: {self.initial_layer_height:.2f}mm)\n"
            f"  - Shell: {self.wall_loops} walls, {self.top_shell_layers} top / {self.bottom_shell_layers} bottom ({self.wall_generator})\n"
            f"  - Infill: {self.sparse_infill_density} {self.sparse_infill_pattern}\n"
            f"  - Thermals: Nozzle {self.nozzle_temperature:.0f}°C, Bed {self.bed_temperature:.0f}°C\n"
            f"  - Speeds: Outer Wall {self.outer_wall_speed_mm_s:.0f} mm/s, Inner Wall {self.inner_wall_speed_mm_s:.0f} mm/s\n"
            f"  - Support: {'Enabled (' + self.support_type + ', ' + self.support_style + ')' if self.enable_support else 'Disabled'}\n"
            f"  - Estimated: ~{self.estimated_filament_grams:.1f}g filament, ~{self.estimated_print_time_mins:.0f} mins\n"
            f"  - Rationale Highlights: {len(self.reasoning)} parameter justifications"
        )

class SettingsEngine:
    """Enterprise rule engine synthesizing multi-objective print profiles."""

    @classmethod
    def optimize(
        cls,
        mesh_or_info: Any,
        objective: OptimizationObjective = OptimizationObjective.BALANCED_QUALITY,
        printer_id: str = "Bambu Lab A1",
        filament_id: str = "pla_basic",
        brand: Optional[str] = None,
        has_connectors: bool = False,
        is_split_flat: bool = False
    ) -> OptimizedSettings:
        """
        Synthesizes physical geometry metrics with material and hardware constraints
        to produce an optimized slicer profile.
        """
        printer = PrinterProfileRegistry.get_profile(printer_id)
        filament = FilamentProfileRegistry.get_profile(filament_id, brand=brand)
        compat = SettingsValidator.validate_pairing(printer, filament)

        # Baseline geometry metrics
        dim_x = 50.0
        dim_y = 50.0
        dim_z = 100.0
        volume_cm3 = 100.0
        if isinstance(mesh_or_info, trimesh.Trimesh):
            dim_x = float(mesh_or_info.extents[0])
            dim_y = float(mesh_or_info.extents[1])
            dim_z = float(mesh_or_info.extents[2])
            volume_cm3 = float(mesh_or_info.volume) / 1000.0 if mesh_or_info.is_watertight else (dim_x * dim_y * dim_z * 0.4 / 1000.0)
        elif hasattr(mesh_or_info, "dim_z"):
            dim_z = float(mesh_or_info.dim_z)
            dim_x = float(getattr(mesh_or_info, "dim_x", dim_z * 0.8))
            dim_y = float(getattr(mesh_or_info, "dim_y", dim_z * 0.8))
            volume_cm3 = float(mesh_or_info.volume_cm3)

        reasoning: Dict[str, str] = {}

        # Check Bambu Lab A1 Build Envelope (256 x 256 x 256 mm)
        max_dim = max(dim_x, dim_y, dim_z)
        if max_dim > 256.0:
            compat.warnings.append(
                f"Model dimensions ({dim_x:.1f} × {dim_y:.1f} × {dim_z:.1f} mm) exceed Bambu Lab A1 build volume (256 × 256 × 256 mm). Scaling down is required."
            )
            reasoning["build_volume"] = f"EXCEEDS BUILD VOLUME: Model max dimension {max_dim:.1f}mm > 256mm build plate limit."

        # 1. Layer Height & Shell Configuration
        if objective == OptimizationObjective.FINE_DETAIL:
            layer_h = 0.12
            walls = 3
            top_layers = 6
            bottom_layers = 5
            infill_pat = "gyroid"
            infill_pct = "15%"
            speed_factor = 0.8
            reasoning["layer_height"] = "0.12mm layer height captures delicate facial features, mudra hands, and fine ornamental contours."
            reasoning["wall_generator"] = "Arachne wall generator dynamically modulates line width to resolve thin tapered structures."

        elif objective == OptimizationObjective.STRONG_FUNCTIONAL:
            layer_h = 0.20
            walls = 5
            top_layers = 5
            bottom_layers = 5
            infill_pat = "gyroid"
            infill_pct = "35%"
            speed_factor = 0.85
            reasoning["layer_height"] = "0.20mm layer height provides thicker polymer bonding ribbons than ultra-fine layers for enhanced tensile strength."
            reasoning["wall_loops"] = "5 wall loops ensure primary mechanical and bending stresses are borne by solid continuous perimeters."
            reasoning["infill"] = "35% Gyroid infill delivers isotropic resistance against multi-directional shear and compression forces."

        elif objective == OptimizationObjective.FAST_PRINTING:
            layer_h = 0.28
            walls = 2
            top_layers = 3
            bottom_layers = 3
            infill_pat = "grid"
            infill_pct = "10%"
            speed_factor = 1.25
            reasoning["layer_height"] = "0.28mm maximizes volumetric deposition rate (70% of 0.4mm nozzle diameter)."
            reasoning["infill"] = "10% Grid infill accelerates print head motion with linear non-curved toolpaths."

        elif objective == OptimizationObjective.MINIMUM_MATERIAL:
            layer_h = 0.20
            walls = 2
            top_layers = 3
            bottom_layers = 3
            infill_pat = "adaptive_cubic"
            infill_pct = "8%"
            speed_factor = 1.0
            reasoning["infill"] = "8% Adaptive Cubic concentrates internal plastic only beneath horizontal surfaces, minimizing wasted internal mass."

        elif objective == OptimizationObjective.SUPPORT_MINIMIZED:
            layer_h = 0.16
            walls = 3
            top_layers = 4
            bottom_layers = 4
            infill_pat = "gyroid"
            infill_pct = "12%"
            speed_factor = 0.9
            reasoning["support"] = "30° threshold angle leverages natural overhang self-support to eliminate unnecessary support columns."

        else:  # BALANCED_QUALITY
            layer_h = 0.16
            walls = 3
            top_layers = 4
            bottom_layers = 4
            infill_pat = "gyroid"
            infill_pct = "15%"
            speed_factor = 1.0
            reasoning["layer_height"] = "0.16mm strikes an optimal trade-off between vertical stair-stepping visibility and total print time."

        # 2. Geometry-Aware Connector Reinforcement
        if has_connectors:
            if walls < 4:
                walls = 4
                reasoning["connectors"] = "Mechanical alignment pins/sockets detected: reinforced wall loops to 4 to provide maximum hoop strength and prevent joint shearing."

        # 3. Miniature & Large Scale Tuning
        brim_t = "outer_only"
        brim_w = 5.0

        outer_speed = round(filament.outer_wall_speed_mm_s * speed_factor, 1)
        inner_speed = round(filament.inner_wall_speed_mm_s * speed_factor, 1)
        infill_speed = round(filament.sparse_infill_speed_mm_s * speed_factor, 1)

        if dim_z < 65.0 and objective != OptimizationObjective.FAST_PRINTING:
            layer_h = min(layer_h, 0.12)
            outer_speed = min(outer_speed, 50.0)
            reasoning["miniature_scale"] = f"Model height ({dim_z:.1f}mm < 65mm) detected as miniature scale: capped layer height at {layer_h:.2f}mm and outer speed at 50mm/s for high-detail facial features."
        elif dim_z > 160.0:
            walls = max(walls, 4)
            brim_w = 6.0
            reasoning["large_statue"] = f"Large model height ({dim_z:.1f}mm > 160mm): reinforced with {walls} wall loops and 6mm outer brim for stability on Textured PEI plate."

        # Aspect ratio stability check
        min_footprint = min(dim_x, dim_y)
        aspect_ratio = dim_z / max(1.0, min_footprint)
        if aspect_ratio > 2.2:
            brim_w = max(brim_w, 6.0)
            reasoning["aspect_ratio"] = f"High aspect ratio ({aspect_ratio:.1f}x height to base): auto-enabled 6mm outer brim to prevent tipping during rapid printer accelerations."

        # 4. Speeds & Thermals
        nozzle_temp = filament.nozzle_temp_recommended
        bed_temp = filament.bed_temp_recommended

        if objective == OptimizationObjective.STRONG_FUNCTIONAL:
            nozzle_temp = min(filament.nozzle_temp_max, nozzle_temp + 5.0)
            reasoning["nozzle_temperature"] = f"+5°C elevated nozzle temperature ({nozzle_temp:.0f}°C) promotes deep polymer chain entanglement between layers."

        # 5. Filament-Specific Tuning
        fil_id = filament.id.lower()
        if "silk" in fil_id:
            outer_speed = min(outer_speed, 45.0)
            reasoning["filament_silk"] = "Silk PLA: reduced outer wall speed to 45mm/s for mirror-like lustrous sheen."
        elif "petg" in fil_id:
            bed_temp = max(bed_temp, 75.0)
            reasoning["filament_petg"] = "PETG: set 75°C textured plate temperature for optimal adhesion."
        elif "tpu" in fil_id:
            outer_speed = min(outer_speed, 35.0)
            inner_speed = min(inner_speed, 45.0)
            reasoning["filament_tpu"] = "TPU: reduced print speeds to 35mm/s for flexible filament feed stability."
        elif "abs" in fil_id:
            brim_w = 8.0
            bed_temp = max(bed_temp, 90.0)
            reasoning["filament_abs"] = "ABS: 8mm outer brim and 90°C bed temperature enforced to prevent thermal contraction corner lifting."

        # 6. Support Strategy
        if is_split_flat:
            supp_enabled = False
            supp_type = "tree(auto)"
            supp_style = "tree_slim"
            supp_z_gap = 0.24
            supp_xy_dist = 0.60
            supp_angle = 30
            reasoning["support_mode"] = "Split components rest flat on cut plane: support structures completely disabled (0% support waste)."
        else:
            supp_enabled = True
            supp_type = "tree(auto)"
            supp_style = "tree_slim"
            if "silk" in fil_id:
                supp_z_gap = 0.26
                reasoning["support_z_gap"] = "Silk PLA: set 0.26mm support top Z gap to prevent glossy layers welding to support interface."
            elif "petg" in fil_id:
                supp_z_gap = 0.28
                reasoning["support_z_gap"] = "PETG: set 0.28mm support top Z gap to prevent aggressive polymer bonding."
            else:
                supp_z_gap = 0.24 if dim_z < 65.0 else 0.22
            supp_xy_dist = 0.60
            supp_angle = 30 if objective == OptimizationObjective.SUPPORT_MINIMIZED else 35
            reasoning["support_style"] = "Tree-slim support columns minimize contact scars on ornamental surfaces while preserving easy manual detachment."

        # 7. Weight & Time Heuristic Estimations (Documented as heuristic models)
        # Material weight estimation based on volume and density
        infill_ratio = float(infill_pct.replace("%", "")) / 100.0
        effective_density_factor = 0.25 + (infill_ratio * 0.40)  # Shells + sparse infill volume fraction
        est_weight_g = round(volume_cm3 * filament.density_g_cm3 * effective_density_factor, 1)

        # Print time estimation based on height, layer count, and speed factor
        total_layers = dim_z / layer_h
        est_time_mins = round((total_layers * 0.18) * (1.0 / speed_factor) + (est_weight_g * 1.2), 0)

        return OptimizedSettings(
            objective=objective,
            printer=printer,
            filament=filament,
            layer_height=layer_h,
            initial_layer_height=0.20,
            wall_loops=walls,
            top_shell_layers=top_layers,
            bottom_shell_layers=bottom_layers,
            sparse_infill_density=infill_pct,
            sparse_infill_pattern=infill_pat,
            nozzle_temperature=nozzle_temp,
            bed_temperature=bed_temp,
            outer_wall_speed_mm_s=outer_speed,
            inner_wall_speed_mm_s=inner_speed,
            sparse_infill_speed_mm_s=infill_speed,
            enable_support=supp_enabled,
            support_type=supp_type,
            support_style=supp_style,
            support_top_z_distance=supp_z_gap,
            support_object_xy_distance=supp_xy_dist,
            support_threshold_angle=supp_angle,
            brim_type=brim_t,
            brim_width_mm=brim_w,
            wall_generator="arachne",
            seam_position="back",
            compatibility=compat,
            reasoning=reasoning,
            estimated_filament_grams=est_weight_g,
            estimated_print_time_mins=est_time_mins
        )

