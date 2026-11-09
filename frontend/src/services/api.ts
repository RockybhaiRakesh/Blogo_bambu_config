import {
  ModelMetadata,
  ComprehensiveAnalysisResponse,
  SplitRecommendationResponse,
  SplitExecutionResponse,
  PrinterProfile,
  FilamentProfile,
  PrintSettingsResponse,
  Generate3MFResponse,
  SlicerCapabilityResponse,
  GCodeTelemetryResponse,
  DashboardStatsResponse
} from '../types';

const BASE_URL = '';

export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  const res = await fetch(`${BASE_URL}/api/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to load dashboard stats');
  return res.json();
}

export async function fetchModels(): Promise<ModelMetadata[]> {
  const res = await fetch(`${BASE_URL}/api/models`);
  if (!res.ok) throw new Error('Failed to load models list');
  return res.json();
}

export async function uploadModelFile(file: File): Promise<{ success: boolean; model: ModelMetadata; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/api/models/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function fetchModel(modelId: string): Promise<ModelMetadata> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}`);
  if (!res.ok) throw new Error('Failed to fetch model metadata');
  return res.json();
}

export async function scaleModel(modelId: string, params: {
  scale_factor?: number;
  target_height_mm?: number;
}): Promise<{
  success: boolean;
  model_id: string;
  scale_factor_applied: number;
  new_dim_x: number;
  new_dim_y: number;
  new_dim_z: number;
  fits_bambu_a1: boolean;
  message: string;
}> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/scale`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Scaling failed' }));
    throw new Error(err.detail || 'Scaling failed');
  }
  return res.json();
}

export async function runModelAnalysis(modelId: string): Promise<ComprehensiveAnalysisResponse> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/analyze`, {
    method: 'POST'
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

export async function fetchSplitRecommendations(modelId: string): Promise<SplitRecommendationResponse> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/split-recommendations`);
  if (!res.ok) throw new Error('Failed to fetch split recommendations');
  return res.json();
}

export async function executeSplit(modelId: string, params: {
  preset?: string;
  cut_z?: number;
  cut_planes?: number[];
  axis?: string;
  connector_type: string;
  clearance_mm?: number;
  pin_radius_mm?: number;
  pin_height_mm?: number;
  magnet_diameter_mm?: number;
  magnet_depth_mm?: number;
  auto_repair?: boolean;
}): Promise<SplitExecutionResponse> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/split`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Splitting failed' }));
    throw new Error(err.detail || 'Splitting failed');
  }
  return res.json();
}

export async function executePaintCut(modelId: string, params: {
  face_indices: number[];
  connector_type: string;
  clearance_mm?: number;
  pin_radius_mm?: number;
  pin_height_mm?: number;
  magnet_diameter_mm?: number;
  magnet_depth_mm?: number;
  auto_repair?: boolean;
}): Promise<SplitExecutionResponse> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/paint-cut`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Paint-to-Cut execution failed' }));
    throw new Error(err.detail || 'Paint-to-Cut execution failed');
  }
  return res.json();
}

export async function fetchSplitParts(modelId: string): Promise<{ has_parts: boolean; parts: any[] }> {
  const res = await fetch(`${BASE_URL}/api/models/${modelId}/parts`);
  if (!res.ok) throw new Error('Failed to fetch parts');
  return res.json();
}

export async function fetchPrinters(): Promise<PrinterProfile[]> {
  const res = await fetch(`${BASE_URL}/api/settings/printers`);
  if (!res.ok) throw new Error('Failed to load printer profiles');
  return res.json();
}

export async function fetchFilaments(): Promise<FilamentProfile[]> {
  const res = await fetch(`${BASE_URL}/api/settings/filaments`);
  if (!res.ok) throw new Error('Failed to load filament profiles');
  return res.json();
}

export async function optimizeSettings(params: {
  printer_id: string;
  filament_id: string;
  objective: string;
  has_connectors: boolean;
  model_id?: string;
}): Promise<PrintSettingsResponse> {
  const res = await fetch(`${BASE_URL}/api/settings/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Settings optimization failed');
  return res.json();
}

export async function generate3MFProject(modelId: string, params: {
  printer_id: string;
  filament_id: string;
  objective: string;
  include_split_parts: boolean;
}): Promise<Generate3MFResponse> {
  const res = await fetch(`${BASE_URL}/api/projects/${modelId}/generate-3mf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '3MF Generation failed' }));
    throw new Error(err.detail || '3MF Generation failed');
  }
  return res.json();
}

export async function fetchSlicerCapabilities(): Promise<SlicerCapabilityResponse> {
  const res = await fetch(`${BASE_URL}/api/slicer/capabilities`);
  if (!res.ok) throw new Error('Failed to probe slicer capabilities');
  return res.json();
}

export async function launchBambuStudio(projectPath: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${BASE_URL}/api/slicer/launch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_path: projectPath })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Launch failed' }));
    throw new Error(err.detail || 'Launch failed');
  }
  return res.json();
}

export async function validateGCode(file?: File, gcodePath?: string): Promise<GCodeTelemetryResponse> {
  let res: Response;
  if (file) {
    const formData = new FormData();
    formData.append('file', file);
    res = await fetch(`${BASE_URL}/api/slicer/validate-gcode`, {
      method: 'POST',
      body: formData
    });
  } else {
    const url = gcodePath ? `${BASE_URL}/api/slicer/validate-gcode?gcode_path=${encodeURIComponent(gcodePath)}` : `${BASE_URL}/api/slicer/validate-gcode`;
    res = await fetch(url, { method: 'POST' });
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'G-code validation failed' }));
    throw new Error(err.detail || 'G-code validation failed');
  }
  return res.json();
}

