"""
Pydantic Schemas for PRINTMATE AI REST API.
Defines strongly-typed request and response structures across the entire print preparation pipeline.
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum

class QualityLevelEnum(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"

class ConnectorTypeEnum(str, Enum):
    CYLINDRICAL = "cylindrical"
    D_SHAPED = "d_shaped"
    KEYED = "keyed"
    DUAL_PIN = "dual_pin"
    ASYMMETRIC = "asymmetric"
    MAGNET_POCKET = "magnet_pocket"
    BALL_JOINT = "ball_joint"
    LOOSE_TENON = "loose_tenon"
    HEXAGONAL = "hexagonal"

class OptimizationObjectiveEnum(str, Enum):
    BALANCED_QUALITY = "balanced_quality"
    MAX_QUALITY = "max_quality"
    FINE_DETAIL = "fine_detail"
    FAST_PRINT = "fast_print"
    FAST_PRINTING = "fast_printing"
    MAX_STRENGTH = "max_strength"
    STRONG_FUNCTIONAL = "strong_functional"
    MIN_SUPPORT = "min_support"

# --- Models & Files ---

class ModelMetadata(BaseModel):
    model_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    format: str
    is_split_part: bool = False
    uploaded_at: str

class ModelUploadResponse(BaseModel):
    success: bool
    model: ModelMetadata
    message: str

class ScaleModelRequest(BaseModel):
    scale_factor: Optional[float] = None
    target_height_mm: Optional[float] = None

class ScaleModelResponse(BaseModel):
    success: bool
    model_id: str
    scale_factor_applied: float
    new_dim_x: float
    new_dim_y: float
    new_dim_z: float
    fits_bambu_a1: bool
    message: str

# --- Geometry & Analysis ---

class GeometrySummary(BaseModel):
    dim_x: float
    dim_y: float
    dim_z: float
    faces: int
    vertices: int
    volume_cm3: float
    surface_area_cm2: float
    is_watertight: bool
    bounds_min: List[float]
    bounds_max: List[float]
    fits_bambu_a1: bool
    scale_category: str

class ThicknessSummary(BaseModel):
    min_thickness_mm: float
    max_thickness_mm: float
    mean_thickness_mm: float
    thin_walls_detected: bool
    thin_region_count: int
    below_nozzle_0_4mm: bool

class OverhangSummary(BaseModel):
    critical_overhang_area_pct: float
    critical_faces_count: int
    requires_supports: bool
    steepest_angle_deg: float

class FragilitySummary(BaseModel):
    fragility_score: float  # 0.0 to 10.0
    fragile_regions_count: int
    is_delicate_miniature: bool
    description: str

class IslandSummary(BaseModel):
    floating_island_count: int
    has_unsupported_minima: bool

class SemanticVisionSummary(BaseModel):
    primary_category: str
    confidence: float
    visual_description: str
    prominent_features: List[str]
    aesthetic_surfaces: List[str]
    provider_used: str

class ComprehensiveAnalysisResponse(BaseModel):
    model_id: str
    geometry: GeometrySummary
    thickness: ThicknessSummary
    overhang: OverhangSummary
    fragility: FragilitySummary
    islands: IslandSummary
    vision: SemanticVisionSummary
    recommended_orientations: List[Dict[str, Any]]
    analysis_time_seconds: float

# --- Splitting & Assembly ---

class SplitRecommendationResponse(BaseModel):
    model_id: str
    exceeds_build_volume: bool
    reasons: List[str]
    recommended_action: str
    suggested_cut_plane_z: float
    suggested_connector: str
    suggested_parts_count: int
    model_height_z: Optional[float] = None

class SplitRequest(BaseModel):
    preset: Optional[str] = "2_piece_waist"
    cut_z: Optional[float] = None
    cut_planes: Optional[List[float]] = None
    axis: Optional[str] = "Z"  # "Z" (Height), "X" (Width/Sagittal), "Y" (Depth/Coronal)
    connector_type: ConnectorTypeEnum = ConnectorTypeEnum.D_SHAPED
    clearance_mm: Optional[float] = None
    pin_radius_mm: Optional[float] = None
    pin_height_mm: Optional[float] = None
    magnet_diameter_mm: Optional[float] = 6.0
    magnet_depth_mm: Optional[float] = 2.0
    quality: QualityLevelEnum = QualityLevelEnum.BALANCED
    auto_repair: Optional[bool] = True

class PaintCutRequest(BaseModel):
    face_indices: List[int]
    connector_type: ConnectorTypeEnum = ConnectorTypeEnum.LOOSE_TENON
    clearance_mm: Optional[float] = 0.20
    magnet_diameter_mm: Optional[float] = 6.0
    magnet_depth_mm: Optional[float] = 2.0
    pin_radius_mm: Optional[float] = 2.5
    pin_height_mm: Optional[float] = 5.0
    auto_repair: Optional[bool] = True

class SplitPartInfo(BaseModel):
    part_id: str
    part_name: str
    filename: str
    file_path: str
    mesh_url: Optional[str] = None
    connector_role: str  # "male", "female", "none"
    dimensions_xyz: List[float]
    triangle_count: int
    fits_bed: bool

class AssemblyStepInfo(BaseModel):
    step_number: int
    title: str
    instructions: str
    warning: Optional[str] = None

class SplitExecutionResponse(BaseModel):
    success: bool
    model_id: str
    parts: List[SplitPartInfo]
    connector_type: str
    clearance_used_mm: float
    pair_validation_passed: bool
    assembly_steps: List[AssemblyStepInfo]
    project_3mf_path: Optional[str] = None

# --- Print Settings ---

class SettingsOptimizeRequest(BaseModel):
    printer_id: str = "bambu_a1"
    filament_id: str = "pla_basic"
    objective: OptimizationObjectiveEnum = OptimizationObjectiveEnum.BALANCED_QUALITY
    has_connectors: bool = False
    model_id: Optional[str] = None

class PrintSettingsResponse(BaseModel):
    printer_name: str
    filament_name: str
    objective: str
    layer_height_mm: float
    initial_layer_height_mm: float
    wall_loops: int
    wall_generator: str
    sparse_infill_density: str
    sparse_infill_pattern: str
    top_shell_layers: int
    bottom_shell_layers: int
    outer_wall_speed_mm_s: float
    inner_wall_speed_mm_s: float
    nozzle_temperature: float
    bed_temperature: float
    enable_support: bool
    support_type: str
    support_style: str
    support_top_z_gap_mm: float
    brim_type: str
    brim_width_mm: float
    estimated_print_time_mins: float
    estimated_filament_grams: float
    is_compatible: bool
    compatibility_errors: List[str]
    compatibility_warnings: List[str]
    engineering_rationale: Dict[str, str]

# --- 3MF Generation & Validation ---

class Generate3MFRequest(BaseModel):
    printer_id: str = "bambu_a1"
    filament_id: str = "pla_basic"
    objective: OptimizationObjectiveEnum = OptimizationObjectiveEnum.BALANCED_QUALITY
    layer_height: Optional[float] = None
    include_split_parts: bool = True

class ProjectValidationSummary(BaseModel):
    is_valid: bool
    status: str
    printer_model: str
    nozzle_diameter: str
    filament_type: str
    layer_height: float
    wall_loops: int
    infill_pattern: str
    support_type: str
    support_top_z_gap: float
    objects_count: int
    object_names: List[str]
    fits_build_plate: bool
    errors: List[str]
    warnings: List[str]

class Generate3MFResponse(BaseModel):
    success: bool
    project_path: str
    filename: str
    download_url: str
    validation: ProjectValidationSummary
    message: str

# --- Slicer & G-code ---

class SlicerCapabilityResponse(BaseModel):
    slicer_name: str
    executable_path: str
    is_installed: bool
    version: Optional[str] = None
    gui_available: bool
    notes: str

class LaunchSlicerRequest(BaseModel):
    project_path: str

class LaunchSlicerResponse(BaseModel):
    success: bool
    status: str
    message: str

class GCodeTelemetryResponse(BaseModel):
    status: str
    is_valid: bool
    filename: str
    slicer_version: str
    total_time_str: str
    total_time_minutes: float
    filament_weight_g: float
    filament_length_mm: float
    total_layers: int
    max_z_height_mm: float
    layer_height_mm: float
    wall_loops: int
    infill_summary: str
    support_summary: str
    support_top_z_gap_mm: float
    support_bottom_z_gap_mm: float
    # Separated coordinates
    model_bounds_x: List[float]
    model_bounds_y: List[float]
    model_bounds_z: List[float]
    support_bounds_x: Optional[List[float]] = None
    support_bounds_y: Optional[List[float]] = None
    brim_bounds_x: Optional[List[float]] = None
    brim_bounds_y: Optional[List[float]] = None
    printed_bounds_x: List[float]
    printed_bounds_y: List[float]
    maintenance_bounds_x: List[float]
    maintenance_bounds_y: List[float]
    fits_build_plate: bool
    is_actual_slicer_output: bool
    errors: List[str]
    warnings: List[str]

# --- Dashboard & System ---

class DashboardStatsResponse(BaseModel):
    total_projects: int
    supported_printers_count: int
    supported_filaments_count: int
    bambu_studio_installed: bool
    bambu_studio_version: Optional[str]
    test_suite_status: str
    verified_tests_count: int
    recent_projects: List[Dict[str, Any]]

