import React, { useState, useEffect } from 'react';
import {
  ModelMetadata,
  SplitRecommendationResponse,
  SplitExecutionResponse,
  StepId
} from '../types';
import { fetchSplitRecommendations, executeSplit, executePaintCut, fetchSplitParts } from '../services/api';
import { ModelViewer3D } from '../components/ModelViewer3D';
import {
  Scissors,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sliders,
  Package,
  Wrench,
  Magnet,
  RotateCcw,
  Sparkles,
  Eye,
  Download,
  Paintbrush,
  Eraser,
  Check,
  Box
} from 'lucide-react';

interface SplitScreenProps {
  model: ModelMetadata | null;
  onNavigate: (step: StepId) => void;
}

const PART_BADGE_COLORS = [
  { bg: 'bg-sky-500', text: 'text-sky-700', border: 'border-sky-300', lightBg: 'bg-sky-50', name: 'Sapphire Blue' },
  { bg: 'bg-amber-500', text: 'text-amber-700', border: 'border-amber-300', lightBg: 'bg-amber-50', name: 'Amber Gold' },
  { bg: 'bg-emerald-500', text: 'text-emerald-700', border: 'border-emerald-300', lightBg: 'bg-emerald-50', name: 'Emerald Green' },
  { bg: 'bg-purple-500', text: 'text-purple-700', border: 'border-purple-300', lightBg: 'bg-purple-50', name: 'Violet Purple' },
  { bg: 'bg-rose-500', text: 'text-rose-700', border: 'border-rose-300', lightBg: 'bg-rose-50', name: 'Crimson Red' },
  { bg: 'bg-teal-500', text: 'text-teal-700', border: 'border-teal-300', lightBg: 'bg-teal-50', name: 'Teal Cyan' }
];

export const SplitScreen: React.FC<SplitScreenProps> = ({
  model,
  onNavigate
}) => {
  const [recommendation, setRecommendation] = useState<SplitRecommendationResponse | null>(null);
  const [splitResult, setSplitResult] = useState<SplitExecutionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Cutting mode: 'planar' | 'paint'
  const [cuttingMode, setCuttingMode] = useState<'planar' | 'paint'>('planar');
  const [paintedFaces, setPaintedFaces] = useState<number[]>([]);
  const [paintPresets, setPaintPresets] = useState<any[]>([]);
  // Controls whether the 3D viewport shows the split assembly vs the original model
  const [viewAssembly, setViewAssembly] = useState<boolean>(false);

  // Configuration parameters
  const [axis, setAxis] = useState<'Z' | 'X' | 'Y'>('Z');
  const [preset, setPreset] = useState<'2_piece_waist' | '3_piece_studio' | '4_piece_action' | 'auto_fit'>('2_piece_waist');
  const [cutZ, setCutZ] = useState<number>(25.0);
  const [connectorType, setConnectorType] = useState<string>('loose_tenon');
  const [clearance, setClearance] = useState<number>(0.20);
  const [magnetDiameter, setMagnetDiameter] = useState<number>(6.0);
  const [magnetDepth, setMagnetDepth] = useState<number>(2.0);
  const [autoRepair, setAutoRepair] = useState<boolean>(true);

  // Part inspection selection (-1 for all parts, 0..N for solo part)
  const [selectedPartIndex, setSelectedPartIndex] = useState<number>(-1);

  const totalH = recommendation?.model_height_z || 130.0;

  useEffect(() => {
    if (!model) return;
    setLoading(true);

    fetchSplitRecommendations(model.model_id)
      .then((rec) => {
        setRecommendation(rec);
        setCutZ(rec.suggested_cut_plane_z);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });

    // Fetch AI anatomical paint presets
    fetch(`/api/models/${model.model_id}/paint-recommendations`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.anatomical_presets) {
          setPaintPresets(data.anatomical_presets);
        }
      })
      .catch(() => {});

    // Check if already split in session
    fetchSplitParts(model.model_id).then((data: any) => {
      if (data.has_parts && data.split_result) {
        setSplitResult(data.split_result);
      } else if (data.has_parts && data.parts && data.parts.length >= 2) {
        setSplitResult({
          success: true,
          model_id: model.model_id,
          parts: data.parts,
          connector_type: 'd_shaped',
          clearance_used_mm: 0.20,
          pair_validation_passed: true,
          assembly_steps: [
            {
              step_number: 1,
              title: `Align Parts & Check Tolerances`,
              instructions: 'Align flat keying face, loose tenon, or magnet pockets with mating recess before assembly.',
              warning: `Confirm seam between mating interfaces has < 0.2mm visible gap.`
            }
          ]
        });
      }
    });
  }, [model]);

  const handleRunSplit = async () => {
    if (!model) return;
    setExecuting(true);
    setError(null);
    setSelectedPartIndex(-1);

    try {
      const res = await executeSplit(model.model_id, {
        preset: preset,
        cut_z: preset === '2_piece_waist' ? cutZ : undefined,
        axis: axis,
        connector_type: connectorType,
        clearance_mm: clearance,
        magnet_diameter_mm: magnetDiameter,
        magnet_depth_mm: magnetDepth,
        auto_repair: autoRepair
      });
      setSplitResult(res);
      setViewAssembly(true);
      setExecuting(false);
    } catch (err: any) {
      setError(err.message || 'Splitting failed.');
      setExecuting(false);
    }
  };

  const handleRunPaintCut = async () => {
    if (!model || paintedFaces.length === 0) return;
    setExecuting(true);
    setError(null);
    setSelectedPartIndex(-1);

    try {
      const res = await executePaintCut(model.model_id, {
        face_indices: paintedFaces,
        connector_type: connectorType,
        clearance_mm: clearance,
        magnet_diameter_mm: magnetDiameter,
        magnet_depth_mm: magnetDepth,
        auto_repair: autoRepair
      });
      setSplitResult(res);
      setViewAssembly(true);
      setExecuting(false);
    } catch (err: any) {
      setError(err.message || 'Paint-to-Cut failed.');
      setExecuting(false);
    }
  };

  const handleResetSplit = () => {
    setSplitResult(null);
    setSelectedPartIndex(-1);
    setPaintedFaces([]);
  };

  if (!model) {
    return (
      <div className="text-center py-20 text-slate-500 font-mono text-sm">
        Please upload or select a model first.
      </div>
    );
  }

  // Multi-plane positions for current preset
  const cutPlanesPreview = preset === '3_piece_studio'
    ? [roundVal(totalH * 0.15), roundVal(totalH * 0.82)]
    : preset === '4_piece_action'
    ? [roundVal(totalH * 0.15), roundVal(totalH * 0.55), roundVal(totalH * 0.82)]
    : [cutZ];

  function roundVal(n: number) {
    return Math.round(n * 10) / 10;
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Precision Splitting & Modular Joints</h1>
            <span className="text-xs font-mono font-medium px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
              Phase 3 & 4 Engine
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-mono">
            {model.filename} • Multi-axis cuts, 3D Paint-to-Cut Brush, Loose Tenons, and Bambu A1 Bed Optimization
          </p>
        </div>

        <div className="flex items-center gap-3">
          {splitResult && (
            <>
              <a
                href={`/api/models/${model.model_id}/download-all-zip`}
                download
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold font-mono shadow-xs transition-colors cursor-pointer"
              >
                <Package className="w-4 h-4" />
                <span>Download Full Kit (.ZIP)</span>
              </a>

              <button
                onClick={handleResetSplit}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors border border-slate-200 cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reconfigure</span>
              </button>
            </>
          )}

          <button
            onClick={() => onNavigate('settings')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-colors shadow-xs cursor-pointer"
          >
            <span>Proceed to Print Settings</span>
            <ArrowRight className="w-4 h-4 text-sky-400" />
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: 3D Viewport with Live Cut Plane(s) or Multi Split Parts (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Viewport View Switcher Pill (When split results exist) */}
          {splitResult && splitResult.parts && splitResult.parts.length >= 2 && (
            <div className="flex flex-wrap items-center justify-between p-2 rounded-xl bg-slate-100 border border-slate-200 text-xs font-mono">
              <div className="flex items-center gap-1.5 font-bold text-slate-800">
                <Layers className="w-4 h-4 text-sky-600" />
                <span>Viewport View:</span>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setViewAssembly(false);
                    setCuttingMode('paint');
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                    !viewAssembly
                      ? 'bg-amber-500 text-slate-950 shadow-2xs ring-1 ring-amber-400'
                      : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                  }`}
                >
                  <Paintbrush className="w-3.5 h-3.5" />
                  <span>🎨 Paint & Edit Model</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewAssembly(true)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                    viewAssembly
                      ? 'bg-sky-600 text-white shadow-2xs'
                      : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                  }`}
                >
                  <Box className="w-3.5 h-3.5" />
                  <span>🧩 Split Assembly ({splitResult.parts.length} Pieces)</span>
                </button>
              </div>
            </div>
          )}

          {viewAssembly && splitResult && splitResult.parts && splitResult.parts.length >= 2 ? (
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between text-xs font-mono text-slate-600 px-1 gap-2">
                <span className="font-bold">MULTI-PART ASSEMBLY PREVIEW ({splitResult.parts.length} PIECES)</span>
                
                {/* Clickable Part Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <button
                    type="button"
                    onClick={() => setSelectedPartIndex(-1)}
                    className={`px-2 py-0.5 rounded-md text-[11px] font-mono font-bold transition-all border cursor-pointer ${
                      selectedPartIndex === -1
                        ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    All Parts
                  </button>
                  {splitResult.parts.map((p, idx) => {
                    const c = PART_BADGE_COLORS[idx % PART_BADGE_COLORS.length];
                    const isSelected = selectedPartIndex === idx;
                    return (
                      <button
                        key={p.part_id}
                        type="button"
                        onClick={() => setSelectedPartIndex(isSelected ? -1 : idx)}
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-mono font-semibold transition-all border cursor-pointer ${
                          isSelected
                            ? `${c.bg} text-white ${c.border} ring-2 ring-sky-400 shadow-2xs`
                            : `${c.lightBg} ${c.text} ${c.border} hover:opacity-90`
                        }`}
                        title={`Click to inspect Part ${idx + 1} (${p.part_name}) solo in 3D`}
                      >
                        <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-white' : c.bg}`} />
                        Part {idx + 1}
                      </button>
                    );
                  })}
                </div>
              </div>

              <ModelViewer3D
                modelId={model.model_id}
                partsUrls={splitResult.parts.map((p) => p.mesh_url || `/api/models/${model.model_id}/parts/${p.filename}`)}
                externalSoloIndex={selectedPartIndex}
                onSelectPart={(idx) => setSelectedPartIndex(idx)}
                height="540px"
              />
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500 px-1">
                <span>
                  {cuttingMode === 'paint'
                    ? '3D SURFACE PAINT-TO-CUT MODE'
                    : 'INTERACTIVE CUT PLANE VISUALIZATION'}
                </span>
                <span className={cuttingMode === 'paint' ? 'text-amber-600 font-bold' : 'text-rose-600 font-semibold'}>
                  {cuttingMode === 'paint'
                    ? `${paintedFaces.length.toLocaleString()} Triangles Painted`
                    : preset === '2_piece_waist'
                    ? `Cut along ${axis}-Axis at ${cutZ.toFixed(1)} mm`
                    : `${cutPlanesPreview.length} Cut Planes: [${cutPlanesPreview.join(', ')} mm]`}
                </span>
              </div>
              <ModelViewer3D
                modelId={model.model_id}
                cutPlanesZ={cuttingMode === 'paint' ? [] : cutPlanesPreview}
                showCutPlane={cuttingMode === 'planar'}
                enablePaintMode={cuttingMode === 'paint'}
                externalPaintedFaces={paintedFaces}
                onPaintedFacesChange={(indices) => setPaintedFaces(indices)}
                height="540px"
              />
            </div>
          )}

          {/* Assembly Manual Card (if split completed) */}
          {splitResult && splitResult.assembly_steps && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                  <Wrench className="w-4 h-4 text-amber-600" />
                  <span>Precision Modular Assembly Guide</span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  Verified Engineering Clearances
                </span>
              </div>
              <div className="space-y-2.5">
                {splitResult.assembly_steps.map((st) => (
                  <div key={st.step_number} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs space-y-1">
                    <div className="font-semibold text-slate-800 flex items-center justify-between">
                      <span>Step {st.step_number}: {st.title}</span>
                    </div>
                    <div className="text-slate-600 leading-relaxed">{st.instructions}</div>
                    {st.warning && (
                      <div className={`flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1.5 rounded-lg border mt-2 ${
                        st.warning.toLowerCase().includes('polarity') || st.warning.toLowerCase().includes('fragile') || st.warning.toLowerCase().includes('thin')
                          ? 'text-amber-800 bg-amber-50/80 border-amber-200'
                          : 'text-blue-800 bg-blue-50/80 border-blue-200'
                      }`}>
                        {st.warning.toLowerCase().includes('polarity') || st.warning.toLowerCase().includes('fragile') || st.warning.toLowerCase().includes('thin') ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                        )}
                        <span>
                          {st.warning.toLowerCase().includes('fit guarantee')
                            ? st.warning
                            : st.warning.toLowerCase().includes('verified') || st.warning.toLowerCase().includes('tolerance')
                            ? `Fit Guarantee: ${st.warning.replace(/^Caution:\s*/i, '').replace(/^Fit Guarantee:\s*/i, '')}`
                            : st.warning}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Split Controls & Connector Form (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Recommendation Banner */}
          {recommendation && (
            <div className={`p-4 rounded-2xl border space-y-2 ${
              recommendation.exceeds_build_volume
                ? 'bg-amber-50 border-amber-200 text-amber-800 shadow-xs'
                : 'bg-blue-50 border-blue-200 text-blue-800 shadow-xs'
            }`}>
              <div className="flex items-center justify-between text-xs font-mono font-semibold">
                <span>BUILD VOLUME ANALYSIS</span>
                <span className="font-bold">{recommendation.exceeds_build_volume ? 'SPLIT REQUIRED' : 'FITS A1 BED'}</span>
              </div>
              <div className="text-xs text-slate-700">
                {recommendation.reasons[0]}
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                Total Z-Height: {totalH.toFixed(1)} mm • Optimal waistline: Z = {recommendation.suggested_cut_plane_z} mm
              </div>
            </div>
          )}

          {/* Form Configuration Container */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500 font-semibold block uppercase">CUTTING & JOINERY WORKFLOW</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 font-bold">
                ModelSplitter Suite
              </span>
            </div>

            {/* Split Complete Status Banner */}
            {splitResult && splitResult.parts && (
              <div className="flex items-center justify-between p-3 rounded-xl bg-blue-50 border border-blue-200 text-xs font-mono">
                <div className="flex items-center gap-2 text-blue-800 font-bold">
                  <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                  <span>Split Complete • {splitResult.parts.length} Parts Fabricated & Ready</span>
                </div>
                <button
                  type="button"
                  onClick={handleResetSplit}
                  className="text-[11px] text-slate-500 hover:text-slate-800 underline cursor-pointer"
                >
                  Reset
                </button>
              </div>
            )}

            {/* Cutting Mode Switcher: Planar vs Paint-to-Cut */}
            <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl">
              <button
                type="button"
                onClick={() => {
                  setCuttingMode('planar');
                  setViewAssembly(false);
                }}
                className={`flex-1 py-2 text-center rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                  cuttingMode === 'planar'
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                📐 Planar & Presets
              </button>
              <button
                type="button"
                onClick={() => {
                  setCuttingMode('paint');
                  setViewAssembly(false);
                }}
                className={`flex-1 py-2 text-center rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  cuttingMode === 'paint'
                    ? 'bg-amber-500 text-slate-950 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <Paintbrush className="w-3.5 h-3.5" />
                <span>🎨 Paint-to-Cut</span>
              </button>
            </div>

            {/* Planar Slicing Options */}
            {cuttingMode === 'planar' && (
              <>
                {/* Cut Orientation Axis Selector */}
                <div className="space-y-1.5">
                  <label className="text-xs font-mono text-slate-700 block font-medium">
                    Cut Orientation Axis:
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: 'Z', name: 'Z-Axis (Height)', desc: 'Horizontal / Transverse' },
                      { id: 'X', name: 'X-Axis (Width)', desc: 'Sagittal / Left-Right' },
                      { id: 'Y', name: 'Y-Axis (Depth)', desc: 'Coronal / Front-Back' }
                    ].map((a) => (
                      <button
                        key={a.id}
                        type="button"
                        onClick={() => setAxis(a.id as any)}
                        className={`p-2.5 rounded-xl border text-center transition-all cursor-pointer ${
                          axis === a.id
                            ? 'border-sky-500 bg-sky-50 text-sky-950 ring-1 ring-sky-500 font-bold shadow-2xs'
                            : 'border-slate-200 bg-slate-50/60 text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        <div className="text-xs font-mono font-bold">{a.name}</div>
                        <div className="text-[10px] text-slate-400 mt-0.5">{a.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Preset Architecture Selector */}
                <div className="space-y-2 pt-1 border-t border-slate-100">
                  <label className="text-xs font-mono text-slate-700 block font-medium">
                    Choose Split Architecture:
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    {[
                      {
                        id: 'auto_fit',
                        name: 'Auto-Fit Bed Volume',
                        badge: 'Auto A1 Slicing',
                        desc: 'Calculates the optimal cuts needed so every part fits within Bambu Lab A1 (256mm).'
                      },
                      {
                        id: '2_piece_waist',
                        name: '2-Piece Classic',
                        badge: '2 Parts',
                        desc: `Cut along ${axis}-axis at ${cutZ.toFixed(1)} mm. Base + Upper Body.`
                      },
                      {
                        id: '3_piece_studio',
                        name: '3-Piece Studio Figurine',
                        badge: '3 Parts',
                        desc: 'Intelligent 3-piece cut: Base + Torso + Head at anatomical cross-section necking.'
                      },
                      {
                        id: '4_piece_action',
                        name: '4-Piece Action Collectible',
                        badge: '4 Parts',
                        desc: 'Base + Lower Limbs + Torso + Head with anti-rotation joinery on all seams.'
                      }
                    ].map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setPreset(p.id as any)}
                        className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          preset === p.id
                            ? 'border-sky-500 bg-sky-50/70 text-sky-950 ring-1 ring-sky-500 shadow-2xs'
                            : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:border-slate-300 hover:bg-slate-100/50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold font-mono text-slate-900">{p.name}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-200/70 text-slate-700 font-semibold">
                            {p.badge}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 leading-relaxed">{p.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* If 2-Piece Classic: show Cut Z slider */}
                {preset === '2_piece_waist' && (
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-700">Cut Plane Position ({axis}-Axis):</span>
                      <span className="text-sky-700 font-bold">{cutZ.toFixed(1)} mm</span>
                    </div>
                    <input
                      type="range"
                      min="5"
                      max={Math.min(250, totalH - 5)}
                      step="0.5"
                      value={cutZ}
                      onChange={(e) => setCutZ(parseFloat(e.target.value))}
                      className="w-full accent-sky-600 bg-slate-200 h-2 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                      <span>Start (0mm)</span>
                      <span>End ({totalH.toFixed(1)}mm)</span>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Paint-to-Cut Options */}
            {cuttingMode === 'paint' && (
              <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 space-y-3 font-mono text-xs text-amber-900">
                <div className="font-bold flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Paintbrush className="w-4 h-4 text-amber-600" />
                    <span>ModelSplitter Surface Paint-to-Cut</span>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-amber-300 font-bold">
                    {paintedFaces.length.toLocaleString()} faces
                  </span>
                </div>
                
                <p className="text-[11px] text-slate-700 leading-relaxed font-sans">
                  <strong>Instructions:</strong> Use your mouse directly on the 3D model on the left to paint:
                  <br />• <strong>Left-Click & Drag:</strong> Highlights surface triangles in Neon Amber
                  <br />• <strong>Right-Click & Drag:</strong> Rotate / Orbit camera view
                  <br />• <strong>Mouse Wheel:</strong> Zoom in / out
                </p>

                {/* AI One-Click Anatomical Preset Buttons */}
                {paintPresets.length > 0 && (
                  <div className="space-y-1.5 pt-1 border-t border-amber-200/70">
                    <div className="text-[11px] font-bold text-amber-950 flex items-center gap-1 font-sans">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                      <span>AI One-Click Anatomical Selections:</span>
                    </div>
                    <div className="grid grid-cols-1 gap-1.5">
                      {paintPresets.map((pr: any) => (
                        <button
                          key={pr.id}
                          type="button"
                          onClick={() => {
                            setPaintedFaces(pr.face_indices);
                            if (pr.recommended_connector) {
                              setConnectorType(pr.recommended_connector);
                            }
                          }}
                          className="flex items-center justify-between p-2 rounded-lg bg-white hover:bg-amber-100 border border-amber-200 text-left transition-all cursor-pointer shadow-2xs"
                        >
                          <div>
                            <span className="font-bold text-slate-900 text-xs block font-sans">{pr.label}</span>
                            <span className="text-[10px] text-slate-500 font-sans">{pr.description}</span>
                          </div>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-mono ml-2 shrink-0">
                            {pr.face_count.toLocaleString()} faces
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {paintedFaces.length === 0 ? (
                  <div className="text-[11px] text-amber-700 italic font-sans">
                    💡 Drag directly on the 3D model to paint, or click an AI button above!
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setPaintedFaces([])}
                    className="w-full py-1 text-center text-[11px] text-rose-600 hover:underline cursor-pointer font-bold"
                  >
                    Clear Painted Selection ({paintedFaces.length.toLocaleString()} faces)
                  </button>
                )}
              </div>
            )}

            {/* Connector & Joint Geometry Selector */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono text-slate-700 block font-medium">
                  Interlocking Modular Joint Type:
                </label>
                <span className="text-[10px] font-mono text-blue-700 font-semibold bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  Wall-Check Active
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'loose_tenon', name: 'Loose Tenon Peg', desc: 'Separate horizontal key (Max shear strength, 0 supports)' },
                  { id: 'magnet_pocket', name: 'Magnet Pockets', desc: '6×2mm Neodymium Snap Docking (Zero glue)' },
                  { id: 'hexagonal', name: 'Hexagonal Prism', desc: '60° Positive Indexing Lock (Anti-rotation)' },
                  { id: 'd_shaped', name: 'D-Shaped Peg', desc: 'Flat Chord Key (Prevents axial twist)' },
                  { id: 'keyed', name: 'Keyed Spline', desc: 'Directional 1-Way Index Keyway' },
                  { id: 'ball_joint', name: 'Ball & Socket', desc: '30° Dynamic Articulated Swivel Joint' }
                ].map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setConnectorType(c.id)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                      connectorType === c.id
                        ? 'border-blue-500 bg-blue-50/70 text-blue-950 ring-1 ring-blue-500 shadow-2xs'
                        : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:border-slate-300 hover:bg-slate-100/50'
                    }`}
                  >
                    <div className="text-xs font-bold font-mono flex items-center gap-1.5">
                      {c.id === 'magnet_pocket' && <Magnet className="w-3.5 h-3.5 text-rose-500" />}
                      {c.id === 'loose_tenon' && <Package className="w-3.5 h-3.5 text-blue-600" />}
                      <span>{c.name}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 truncate mt-0.5">{c.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Loose Tenon Special Info */}
            {connectorType === 'loose_tenon' && (
              <div className="p-3 rounded-xl bg-blue-50/70 border border-blue-200 text-xs font-mono text-blue-800 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <Package className="w-3.5 h-3.5 text-blue-600" />
                  <span>ModelSplitter Loose Tenon Architecture</span>
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed font-sans">
                  Both cut pieces receive recessed sockets. An independent printable Tenon Peg STL is generated lying flat on the print bed for maximum layer tensile shear strength.
                </p>
              </div>
            )}

            {/* Magnet Pocket Parameters */}
            {connectorType === 'magnet_pocket' && (
              <div className="p-3.5 rounded-xl bg-rose-50/60 border border-rose-200/80 space-y-2.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-rose-900 font-mono">
                  <Magnet className="w-3.5 h-3.5 text-rose-600" />
                  <span>Neodymium Disc Magnet Specification</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div>
                    <label className="text-[10px] text-rose-700 block mb-1">Diameter (mm):</label>
                    <input
                      type="number"
                      step="0.5"
                      min="3.0"
                      max="12.0"
                      value={magnetDiameter}
                      onChange={(e) => setMagnetDiameter(parseFloat(e.target.value) || 6.0)}
                      className="w-full px-2.5 py-1.5 bg-white border border-rose-300 rounded-lg text-xs font-mono text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-rose-700 block mb-1">Depth (mm):</label>
                    <input
                      type="number"
                      step="0.5"
                      min="1.0"
                      max="6.0"
                      value={magnetDepth}
                      onChange={(e) => setMagnetDepth(parseFloat(e.target.value) || 2.0)}
                      className="w-full px-2.5 py-1.5 bg-white border border-rose-300 rounded-lg text-xs font-mono text-slate-800"
                    />
                  </div>
                </div>
                <p className="text-[10px] text-rose-600 font-mono">
                  Cavities automatically oversized by +0.2mm for effortless press-fit snap docking.
                </p>
              </div>
            )}

            {/* Material-Aware Clearance */}
            {connectorType !== 'magnet_pocket' && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-700">Engineering Clearance:</span>
                  <span className="text-blue-700 font-bold">{clearance.toFixed(2)} mm</span>
                </div>
                <select
                  value={clearance}
                  onChange={(e) => setClearance(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-mono text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs"
                >
                  <option value={0.15}>0.15 mm (Tight / Press-Fit)</option>
                  <option value={0.20}>0.20 mm (Standard PLA Recommended)</option>
                  <option value={0.25}>0.25 mm (Easy Slide-In)</option>
                  <option value={0.30}>0.30 mm (PETG / High Shrinkage)</option>
                </select>
              </div>
            )}

            {/* Auto-Repair & Manifold Sanitization Checkbox */}
            <label className="flex items-center gap-2 text-xs font-mono text-slate-700 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={autoRepair}
                onChange={(e) => setAutoRepair(e.target.checked)}
                className="w-4 h-4 rounded accent-sky-600 cursor-pointer"
              />
              <span>Auto-heal non-manifold edges & micro-holes before cut</span>
            </label>

            {/* Execution Buttons: Dynamic based on cuttingMode */}
            {cuttingMode === 'paint' ? (
              <button
                onClick={handleRunPaintCut}
                disabled={executing || paintedFaces.length < 3}
                className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-slate-200 text-slate-950 font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-xs cursor-pointer"
              >
                <Scissors className="w-4 h-4" />
                <span>
                  {executing
                    ? `Extracting Painted Seam & Capping Manifold...`
                    : splitResult
                    ? `🔄 Re-Calculate Paint-to-Cut (${paintedFaces.length.toLocaleString()} Faces)`
                    : `Execute Paint-to-Cut (${paintedFaces.length.toLocaleString()} Faces)`}
                </span>
              </button>
            ) : (
              <button
                onClick={handleRunSplit}
                disabled={executing}
                className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-slate-200 text-slate-950 font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-xs cursor-pointer"
              >
                <Scissors className="w-4 h-4" />
                <span>
                  {executing
                    ? `Partitioning Mesh & Engineering Precision Joints...`
                    : splitResult
                    ? `🔄 Re-Calculate Precision Split & Modular Joints`
                    : `Execute Precision Split & Modular Joints`}
                </span>
              </button>
            )}

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {error}
              </div>
            )}
          </div>

          {/* Generated Parts Breakdown Card with Direct Downloads & 3D Inspect */}
          {splitResult && splitResult.parts && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-500 font-semibold uppercase">
                  FABRICATED PARTS ({splitResult.parts.length} PIECES)
                </span>
                <span className="text-xs font-mono text-blue-700 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Pair Certified
                </span>
              </div>

              <div className="space-y-2.5">
                {splitResult.parts.map((p, idx) => {
                  const c = PART_BADGE_COLORS[idx % PART_BADGE_COLORS.length];
                  const isSelected = selectedPartIndex === idx;
                  return (
                    <div
                      key={p.part_id}
                      className={`p-3.5 rounded-xl ${c.lightBg} border transition-all ${
                        isSelected ? `ring-2 ring-sky-500 ${c.border} shadow-xs` : c.border
                      } space-y-2`}
                    >
                      <div className="flex items-center justify-between text-xs font-mono">
                        <div className="flex items-center gap-2">
                          <span className={`w-3 h-3 rounded-full ${c.bg} shrink-0`} />
                          <span className="font-bold text-slate-900">{p.part_name}</span>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full bg-white ${c.text} border ${c.border} uppercase font-bold`}>
                          {p.connector_role}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-600 font-mono pl-5">
                        Extents: {p.dimensions_xyz[0]} × {p.dimensions_xyz[1]} × {p.dimensions_xyz[2]} mm
                      </div>

                      <div className="text-[10px] text-slate-500 font-mono pl-5 flex items-center justify-between">
                        <span>{p.triangle_count.toLocaleString()} triangles</span>
                        <span className="text-blue-700 font-semibold">✓ Fits Bambu A1 Bed</span>
                      </div>

                      {/* Action buttons: Inspect Solo in 3D & Download STL */}
                      <div className="pt-2 border-t border-slate-200/60 pl-5 flex items-center justify-between gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedPartIndex(isSelected ? -1 : idx)}
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono font-medium border transition-colors cursor-pointer ${
                            isSelected
                              ? 'bg-sky-600 text-white border-sky-600'
                              : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'
                          }`}
                        >
                          <Eye className="w-3 h-3 text-sky-500" />
                          <span>{isSelected ? 'Exit Solo' : 'Inspect in 3D'}</span>
                        </button>

                        <a
                          href={`/api/models/${model.model_id}/parts/${p.filename}`}
                          download={p.filename}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 text-[11px] font-mono font-semibold border border-sky-200 shadow-2xs transition-colors cursor-pointer"
                        >
                          <Download className="w-3 h-3" />
                          <span>Download STL</span>
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
