import React, { useState, useEffect } from 'react';
import { ModelMetadata, Generate3MFResponse, PrintSettingsResponse, StepId } from '../types';
import { generate3MFProject, launchBambuStudio, optimizeSettings, runModelAnalysis } from '../services/api';
import {
  Package,
  HardDrive,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileCheck,
  Clock,
  Printer,
  Sparkles,
  Sliders,
  Thermometer,
  Flame,
  Layers,
  Box,
  Check,
  Info
} from 'lucide-react';

interface ProjectScreenProps {
  model: ModelMetadata | null;
  onNavigate: (step: StepId) => void;
}

const FILAMENT_OPTIONS = [
  {
    id: 'pla_basic',
    name: 'Bambu PLA Basic',
    badge: 'Recommended',
    temp: '220°C / 65°C',
    desc: 'Standard high-reliability PLA for general figures and rapid prototyping.'
  },
  {
    id: 'pla_matte',
    name: 'Bambu PLA Matte',
    badge: 'Velvety Finish',
    temp: '220°C / 65°C',
    desc: 'Matte surface hides layer lines; ideal for decorative figurines.'
  },
  {
    id: 'pla_silk',
    name: 'Bambu PLA Silk',
    badge: 'High Gloss Sheen',
    temp: '225°C / 65°C',
    desc: 'Glossy metallic sheen. Auto-sets 0.26mm Z-gap to prevent support welding.'
  },
  {
    id: 'pla_silk_plus_gold',
    name: 'PLA SILK+ Gold',
    badge: 'Your Spool (208°C)',
    temp: '208°C / 55°C',
    desc: 'Calibrated for your 200-220°C Gold Silk spool. 40mm/s wall gloss & 0.26mm anti-stick support gap.'
  },
  {
    id: 'petg',
    name: 'Bambu PETG-HF / Basic',
    badge: 'Tough & Heat Res',
    temp: '255°C / 75°C',
    desc: 'High impact and weather resistance. Auto-sets 0.28mm safe support gap.'
  },
  {
    id: 'abs',
    name: 'Bambu ABS',
    badge: 'High Thermal',
    temp: '260°C / 90°C',
    desc: 'Engineering polymer. Auto-enables 8mm outer brim to prevent corner warp.'
  },
  {
    id: 'tpu',
    name: 'Bambu TPU 95A',
    badge: 'Flexible Elastic',
    temp: '230°C / 35°C',
    desc: 'Flexible elastomer. Slow 35mm/s extrusion speed for feed stability.'
  }
];

const OBJECTIVE_OPTIONS = [
  {
    id: 'balanced_quality',
    title: 'Balanced Quality',
    desc: 'Auto 0.12–0.16mm layers with Gyroid infill. Ideal for standard figurines.'
  },
  {
    id: 'fine_detail',
    title: 'Fine Detail Figurine',
    desc: 'Auto 0.08–0.12mm layers with Arachne dynamic thin walls for faces & hands.'
  },
  {
    id: 'fast_printing',
    title: 'Fast Print Speed',
    desc: '0.20–0.28mm layers for rapid prototyping and concept verification.'
  },
  {
    id: 'strong_functional',
    title: 'Maximum Strength',
    desc: '4–5 solid perimeter wall loops and 35% isotropic Gyroid infill.'
  }
];

export const ProjectScreen: React.FC<ProjectScreenProps> = ({
  model,
  onNavigate
}) => {
  const [selectedFilament, setSelectedFilament] = useState<string>('pla_basic');
  const [selectedObjective, setSelectedObjective] = useState<string>('balanced_quality');
  const [useSplitParts, setUseSplitParts] = useState<boolean>(false);

  const [liveSettings, setLiveSettings] = useState<PrintSettingsResponse | null>(null);
  const [modelDims, setModelDims] = useState<{ x: number; y: number; z: number; vol: number; fits: boolean } | null>(null);
  const [loadingRecipe, setLoadingRecipe] = useState<boolean>(false);

  const [project, setProject] = useState<Generate3MFResponse | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [launching, setLaunching] = useState<boolean>(false);
  const [launchMsg, setLaunchMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load model dimensions on mount
  useEffect(() => {
    if (!model) return;
    runModelAnalysis(model.model_id)
      .then((data) => {
        setModelDims({
          x: data.geometry.dim_x,
          y: data.geometry.dim_y,
          z: data.geometry.dim_z,
          vol: data.geometry.volume_cm3,
          fits: data.geometry.fits_bambu_a1
        });
      })
      .catch(() => {});
  }, [model]);

  // Dynamically update optimized recipe when filament, objective, or model changes
  useEffect(() => {
    if (!model) return;
    setLoadingRecipe(true);
    optimizeSettings({
      printer_id: 'bambu_lab_a1',
      filament_id: selectedFilament,
      objective: selectedObjective,
      has_connectors: false,
      model_id: model.model_id
    })
      .then((res) => {
        setLiveSettings(res);
        setLoadingRecipe(false);
      })
      .catch((err) => {
        console.error(err);
        setLoadingRecipe(false);
      });
  }, [model, selectedFilament, selectedObjective]);

  const handleGenerate3MF = async () => {
    if (!model) return;
    setGenerating(true);
    setError(null);
    setLaunchMsg(null);

    try {
      const res = await generate3MFProject(model.model_id, {
        printer_id: 'bambu_lab_a1',
        filament_id: selectedFilament,
        objective: selectedObjective,
        include_split_parts: useSplitParts
      });
      setProject(res);
      setGenerating(false);
    } catch (err: any) {
      setError(err.message || 'Failed to generate 3MF project.');
      setGenerating(false);
    }
  };

  const handleLaunchStudio = async () => {
    if (!project) return;
    setLaunching(true);
    setLaunchMsg(null);

    try {
      const res = await launchBambuStudio(project.project_path);
      setLaunchMsg(res.message);
      setLaunching(false);
    } catch (err: any) {
      setLaunchMsg(`Launch failed: ${err.message}`);
      setLaunching(false);
    }
  };

  if (!model) {
    return (
      <div className="text-center py-20 text-slate-500 font-mono text-sm">
        Please upload or select a model first.
      </div>
    );
  }

  const isMiniature = modelDims ? modelDims.z < 65.0 : false;
  const isLarge = modelDims ? modelDims.z > 160.0 : false;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn pb-12">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Print Preparation Studio & Bambu A1 Packaging
            </h1>
            <span className="text-xs font-mono font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Native Bambu Studio 3MF
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-mono">
            {model.filename} • Customized automatically based on model size, filament material, and Bambu Lab A1 hardware
          </p>
        </div>

        <button
          onClick={() => onNavigate('slicer')}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors border border-slate-300 shadow-2xs"
        >
          <span>Slice & G-code Verification</span>
          <ArrowRight className="w-4 h-4 text-blue-600" />
        </button>
      </div>

      {/* Grid: Left Column (Size, Filament & Objective) / Right Column (Live Recipe & 1-Click Action) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Card 1: Model Size & Bed Envelope Status */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center text-sky-600 border border-sky-100">
                  <Box className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Model Dimensions & Build Plate Fit</h3>
                  <p className="text-[11px] text-slate-500 font-mono">Target: Bambu Lab A1 (256 × 256 × 256 mm)</p>
                </div>
              </div>

              {modelDims && (
                <span
                  className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full border ${
                    modelDims.fits
                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {modelDims.fits ? '✓ Fits 256mm Bed' : '⚠️ Exceeds 256mm'}
                </span>
              )}
            </div>

            {modelDims ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">WIDTH (X)</span>
                  <span className="font-bold text-slate-900 text-sm">{modelDims.x} mm</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">DEPTH (Y)</span>
                  <span className="font-bold text-slate-900 text-sm">{modelDims.y} mm</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">HEIGHT (Z)</span>
                  <span className="font-bold text-sky-700 text-sm">{modelDims.z} mm</span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">VOLUME</span>
                  <span className="font-bold text-slate-900 text-sm">{modelDims.vol} cm³</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 font-mono animate-pulse">Inspecting model dimensions...</div>
            )}

            <div className="flex items-center justify-between text-xs font-mono pt-1 text-slate-600">
              <span>
                Scale Classification:{' '}
                <strong className="text-slate-900">
                  {isMiniature ? 'Tabletop Miniature (<65mm)' : isLarge ? 'Large Display Statue (>160mm)' : 'Standard Figurine (65–160mm)'}
                </strong>
              </span>
              <button
                onClick={() => onNavigate('analyze')}
                className="text-sky-600 hover:text-sky-700 hover:underline font-semibold"
              >
                Change Scale / Inspect 3D ➔
              </button>
            </div>
          </div>

          {/* Card 2: Filament Material Selector */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Filament Material Profile</h3>
                <p className="text-[11px] text-slate-500">
                  Select your spool. Thermals, cooling, and safe tree support Z-gaps calibrate automatically.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {FILAMENT_OPTIONS.map((fil) => {
                const isSelected = selectedFilament === fil.id;
                return (
                  <div
                    key={fil.id}
                    onClick={() => setSelectedFilament(fil.id)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/50 shadow-2xs'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-900 font-mono">{fil.name}</span>
                      {isSelected ? (
                        <div className="w-4 h-4 rounded-full bg-blue-600 flex items-center justify-center text-white">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      ) : (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                          {fil.badge}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] font-mono text-blue-700 font-medium mb-1">{fil.temp}</div>
                    <p className="text-[11px] text-slate-500 leading-tight">{fil.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card 3: Print Objective Selector */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600 border border-purple-100">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Print Quality Objective</h3>
                <p className="text-[11px] text-slate-500">Balances layer heights, perimeter wall loops, and infill.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {OBJECTIVE_OPTIONS.map((obj) => {
                const isSelected = selectedObjective === obj.id;
                return (
                  <div
                    key={obj.id}
                    onClick={() => setSelectedObjective(obj.id)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-purple-500 bg-purple-50/40 shadow-2xs'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-900">{obj.title}</span>
                      {isSelected && (
                        <div className="w-4 h-4 rounded-full bg-purple-600 flex items-center justify-center text-white">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 leading-tight">{obj.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Live Recipe & 1-Click Generation Action */}
        <div className="lg:col-span-5 space-y-6">
          {/* Live Optimized Recipe Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 space-y-5 shadow-xs sticky top-20">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-bold text-slate-900 font-mono uppercase tracking-wider">
                  AI Dynamic Print Recipe
                </h3>
              </div>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                Bambu Lab A1 • 0.4 Nozzle
              </span>
            </div>

            {liveSettings ? (
              <div className="space-y-4">
                {/* 6 Key Parameter Tiles */}
                <div className="grid grid-cols-2 gap-2.5 font-mono text-xs">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">LAYER HEIGHT</span>
                    <span className="font-bold text-slate-900 text-sm">{liveSettings.layer_height_mm} mm</span>
                    <span className="text-[10px] text-slate-500 block">Initial: {liveSettings.initial_layer_height_mm}mm</span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">WALL LOOPS</span>
                    <span className="font-bold text-slate-900 text-sm">{liveSettings.wall_loops} Loops</span>
                    <span className="text-[10px] text-slate-500 block uppercase">{liveSettings.wall_generator} Engine</span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">TREE SUPPORT</span>
                    <span className="font-bold text-blue-700 text-sm">Tree Slim (Auto)</span>
                    <span className="text-[10px] text-slate-500 block">Top Z-Gap: {liveSettings.support_top_z_gap_mm}mm</span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">INFILL PATTERN</span>
                    <span className="font-bold text-slate-900 text-sm">{liveSettings.sparse_infill_density}</span>
                    <span className="text-[10px] text-slate-500 block capitalize">{liveSettings.sparse_infill_pattern}</span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">NOZZLE TEMP</span>
                    <span className="font-bold text-slate-900 text-sm">{liveSettings.nozzle_temperature}°C</span>
                    <span className="text-[10px] text-slate-500 block">0.4mm Brass/Hardened</span>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                    <span className="text-[10px] text-slate-400 block">PEI BED TEMP</span>
                    <span className="font-bold text-slate-900 text-sm">{liveSettings.bed_temperature}°C</span>
                    <span className="text-[10px] text-slate-500 block">Textured PEI Plate</span>
                  </div>
                </div>

                {/* Brim & Adhesion Status */}
                <div className="p-3 bg-blue-50/70 border border-blue-200/80 rounded-xl text-xs font-mono flex items-center justify-between text-blue-900">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                    <span>Bed Adhesion: {liveSettings.brim_type} ({liveSettings.brim_width_mm}mm)</span>
                  </span>
                  <span className="text-[11px] text-blue-700">Zero Warping</span>
                </div>

                {/* Heuristic Estimations */}
                <div className="flex items-center justify-between text-xs font-mono text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div>
                    <span className="text-slate-400 block text-[10px]">EST. FILAMENT</span>
                    <strong className="text-slate-800">~{liveSettings.estimated_filament_grams} g</strong>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[10px]">EST. TIME</span>
                    <strong className="text-slate-800">~{Math.round(liveSettings.estimated_print_time_mins / 60)}h {Math.round(liveSettings.estimated_print_time_mins % 60)}m</strong>
                  </div>
                </div>

                {/* Justification Bullet Points */}
                <div className="space-y-1.5 pt-1">
                  <span className="text-[11px] font-mono text-slate-400 font-semibold uppercase block">
                    Engineering Rationale
                  </span>
                  {Object.entries(liveSettings.engineering_rationale).slice(0, 3).map(([key, reason]) => (
                    <div key={key} className="text-[11px] text-slate-600 leading-snug flex items-start gap-1.5">
                      <span className="text-blue-500 font-bold">•</span>
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs font-mono text-slate-400 animate-pulse">
                Synthesizing multi-variable print profile...
              </div>
            )}

            {/* Optional Advanced Split Parts Toggle */}
            <div className="pt-2 border-t border-slate-100">
              <label className="flex items-center gap-2 text-xs font-mono text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useSplitParts}
                  onChange={(e) => setUseSplitParts(e.target.checked)}
                  className="accent-blue-600 rounded bg-slate-100"
                />
                <span>Package Interlocking Split Parts (Optional)</span>
              </label>
            </div>

            {/* Primary Action Button */}
            <button
              onClick={handleGenerate3MF}
              disabled={generating}
              className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white font-bold text-sm transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 cursor-pointer"
            >
              <Package className="w-5 h-5" />
              <span>{generating ? 'Injecting Bambu Settings & Packaging 3MF...' : 'Generate Validated Bambu 3MF'}</span>
            </button>

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {error}
              </div>
            )}

            {/* Generated Output Actions */}
            {project && (
              <div className="space-y-3 pt-3 border-t border-slate-100 animate-fadeIn">
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-800 text-xs font-mono flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                  <span className="font-semibold">3MF Project Ready for Bambu Studio!</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <a
                    href={project.download_url}
                    className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-blue-300 text-slate-800 transition-all flex items-center justify-between shadow-2xs group"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:scale-105 transition-transform border border-blue-100">
                        <HardDrive className="w-4 h-4" />
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-bold font-mono text-slate-900">Download .3MF</div>
                        <div className="text-[10px] text-slate-400 font-mono truncate max-w-[100px]">Save File</div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 transition-colors" />
                  </a>

                  <button
                    onClick={handleLaunchStudio}
                    disabled={launching}
                    className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-blue-300 text-slate-800 transition-all flex items-center justify-between shadow-2xs group text-left cursor-pointer"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:scale-105 transition-transform border border-blue-100">
                        <ExternalLink className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold font-mono text-slate-900">Open Studio</div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {launching ? 'Launching...' : 'Desktop App'}
                        </div>
                      </div>
                    </div>
                    <Printer className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 transition-colors" />
                  </button>
                </div>

                {launchMsg && (
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs font-mono flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-blue-600" />
                    <span>{launchMsg}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
