export interface ModelMetadata {
  model_id: string;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  format: string;
  is_split_part: boolean;
  uploaded_at: string;
}

export interface GeometrySummary {
  dim_x: number;
  dim_y: number;
  dim_z: number;
  faces: number;
  vertices: number;
  volume_cm3: number;
  surface_area_cm2: number;
  is_watertight: boolean;
  bounds_min: number[];
  bounds_max: number[];
  fits_bambu_a1: boolean;
  scale_category: string;
}

export interface ThicknessSummary {
  min_thickness_mm: number;
  max_thickness_mm: number;
  mean_thickness_mm: number;
  thin_walls_detected: boolean;
  thin_region_count: number;
  below_nozzle_0_4mm: boolean;
}

export interface OverhangSummary {
  critical_overhang_area_pct: number;
  critical_faces_count: number;
  requires_supports: boolean;
  steepest_angle_deg: number;
}

export interface FragilitySummary {
  fragility_score: number;
  fragile_regions_count: number;
  is_delicate_miniature: boolean;
  description: string;
}

export interface IslandSummary {
  floating_island_count: number;
  has_unsupported_minima: boolean;
}

export interface SemanticVisionSummary {
  primary_category: string;
  confidence: number;
  visual_description: string;
  prominent_features: string[];
  aesthetic_surfaces: string[];
  provider_used: string;
}

export interface ComprehensiveAnalysisResponse {
  model_id: string;
  geometry: GeometrySummary;
  thickness: ThicknessSummary;
  overhang: OverhangSummary;
  fragility: FragilitySummary;
  islands: IslandSummary;
  vision: SemanticVisionSummary;
  recommended_orientations: Array<{
    rank: number;
    name: string;
    score: number;
    overhang_area_cm2: number;
    bed_contact_area_cm2: number;
    height_mm: number;
    explanation: string;
  }>;
  analysis_time_seconds: number;
}

export interface SplitRecommendationResponse {
  model_id: string;
  exceeds_build_volume: boolean;
  reasons: string[];
  recommended_action: string;
  suggested_cut_plane_z: number;
  suggested_connector: string;
  suggested_parts_count: number;
  model_height_z?: number;
}

export interface SplitPartInfo {
  part_id: string;
  part_name: string;
  filename: string;
  file_path: string;
  mesh_url?: string;
  connector_role: string;
  dimensions_xyz: number[];
  triangle_count: number;
  fits_bed: boolean;
}

export interface AssemblyStepInfo {
  step_number: number;
  title: string;
  instructions: string;
  warning?: string;
}

export interface SplitExecutionResponse {
  success: boolean;
  model_id: string;
  parts: SplitPartInfo[];
  connector_type: string;
  clearance_used_mm: number;
  pair_validation_passed: boolean;
  assembly_steps: AssemblyStepInfo[];
  project_3mf_path?: string;
}

export interface PrinterProfile {
  id: string;
  name: string;
  manufacturer: string;
  build_volume_mm: number[];
  nozzle_diameter_mm: number;
  bed_type: string;
  is_default: boolean;
}

export interface FilamentProfile {
  id: string;
  brand: string;
  material_name: string;
  category: string;
  nozzle_temp_range: number[];
  bed_temp_range: number[];
  density_g_cm3: number;
  max_volumetric_speed_mm3_s: number;
  requires_enclosure: boolean;
  is_default: boolean;
}

export interface PrintSettingsResponse {
  printer_name: string;
  filament_name: string;
  objective: string;
  layer_height_mm: number;
  initial_layer_height_mm: number;
  wall_loops: number;
  wall_generator: string;
  sparse_infill_density: string;
  sparse_infill_pattern: string;
  top_shell_layers: number;
  bottom_shell_layers: number;
  outer_wall_speed_mm_s: number;
  inner_wall_speed_mm_s: number;
  nozzle_temperature: number;
  bed_temperature: number;
  enable_support: boolean;
  support_type: string;
  support_style: string;
  support_top_z_gap_mm: number;
  brim_type: string;
  brim_width_mm: number;
  estimated_print_time_mins: number;
  estimated_filament_grams: number;
  is_compatible: boolean;
  compatibility_errors: string[];
  compatibility_warnings: string[];
  engineering_rationale: Record<string, string>;
}

export interface ProjectValidationSummary {
  is_valid: boolean;
  status: string;
  printer_model: string;
  nozzle_diameter: string;
  filament_type: string;
  layer_height: number;
  wall_loops: number;
  infill_pattern: string;
  support_type: string;
  support_top_z_gap: number;
  objects_count: number;
  object_names: string[];
  fits_build_plate: boolean;
  errors: string[];
  warnings: string[];
}

export interface Generate3MFResponse {
  success: boolean;
  project_path: string;
  filename: string;
  download_url: string;
  validation: ProjectValidationSummary;
  message: string;
}

export interface SlicerCapabilityResponse {
  slicer_name: string;
  executable_path: string;
  is_installed: boolean;
  version?: string;
  gui_available: boolean;
  notes: string;
}

export interface GCodeTelemetryResponse {
  status: string;
  is_valid: boolean;
  filename: string;
  slicer_version: string;
  total_time_str: string;
  total_time_minutes: number;
  filament_weight_g: number;
  filament_length_mm: number;
  total_layers: number;
  max_z_height_mm: number;
  layer_height_mm: number;
  wall_loops: number;
  infill_summary: string;
  support_summary: string;
  support_top_z_gap_mm: number;
  support_bottom_z_gap_mm: number;
  model_bounds_x: number[];
  model_bounds_y: number[];
  model_bounds_z: number[];
  support_bounds_x?: number[];
  support_bounds_y?: number[];
  brim_bounds_x?: number[];
  brim_bounds_y?: number[];
  printed_bounds_x: number[];
  printed_bounds_y: number[];
  maintenance_bounds_x: number[];
  maintenance_bounds_y: number[];
  fits_build_plate: boolean;
  is_actual_slicer_output: boolean;
  errors: string[];
  warnings: string[];
}

export interface DashboardStatsResponse {
  total_projects: number;
  supported_printers_count: number;
  supported_filaments_count: number;
  bambu_studio_installed: boolean;
  bambu_studio_version?: string;
  test_suite_status: string;
  verified_tests_count: number;
  recent_projects: Array<{
    name: string;
    path: string;
    size_mb: number;
    modified: number;
  }>;
}

export type StepId = 'dashboard' | 'upload' | 'analyze' | 'split' | 'settings' | 'project' | 'slicer';
