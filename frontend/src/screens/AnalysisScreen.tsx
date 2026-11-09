import React, { useState, useEffect } from 'react';
import { ModelMetadata, ComprehensiveAnalysisResponse, StepId } from '../types';
import { runModelAnalysis, scaleModel } from '../services/api';
import { ModelViewer3D } from '../components/ModelViewer3D';
import {
  Cpu,
  Box,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Scissors,
  Sliders,
  Sparkles,
  Maximize2,
  Package,
  Compass,
  Eye,
  Info
} from 'lucide-react';

interface AnalysisScreenProps {
  model: ModelMetadata | null;
  onNavigate: (step: StepId) => void;
}

export const AnalysisScreen: React.FC<AnalysisScreenProps> = ({
  model,
  onNavigate
}) => {
  const [analysis, setAnalysis] = useState<ComprehensiveAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [scaling, setScaling] = useState<boolean>(false);
  const [customZ, setCustomZ] = useState<string>('');
  const [viewerKey, setViewerKey] = useState<number>(0);

  const handleScale = async (factor?: number, targetZ?: number) => {
    if (!model) return;
    setScaling(true);
    try {
      await scaleModel(model.model_id, {
        scale_factor: factor,
        target_height_mm: targetZ
      });
      // Re-run analysis with freshly scaled geometry
      const freshData = await runModelAnalysis(model.model_id);
      setAnalysis(freshData);
      setViewerKey((k) => k + 1);
      setScaling(false);
      setCustomZ('');
    } catch (err: any) {
      console.error(err);
      alert(err.message || 'Failed to scale model.');
      setScaling(false);
    }
  };

  useEffect(() => {
    if (!model) return;
    setLoading(true);
    setError(null);

    runModelAnalysis(model.model_id)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message || 'Failed to analyze 3D geometry.');
        setLoading(false);
      });
  }, [model]);

  if (!model) {
    return (
      <div className="text-center py-20 space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mx-auto">
          <Box className="w-8 h-8" />
        </div>
        <h2 className="text-lg font-bold text-slate-900">No Model Selected</h2>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Please upload a 3D model or select a preloaded model to run geometry intelligence.
        </p>
        <button
          onClick={() => onNavigate('upload')}
          className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-colors shadow-xs"
        >
          Go to Model Upload
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Geometry Intelligence & AI Vision</h1>
            <span className="text-xs font-mono font-medium px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
              Phase 1 & 2 Engine
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-mono">
            Analyzing {model.filename} • {(model.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
          </p>
          <div className="mt-1 flex items-center gap-1.5 text-[11px] font-mono text-slate-500">
            <span className="text-slate-400">Disk Location:</span>
            <code className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200 select-all" title={model.file_path}>
              {model.file_path}
            </code>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('project')}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-md shadow-blue-600/20 cursor-pointer"
          >
            <Package className="w-4 h-4" />
            <span>Configure Print & 3MF (Bambu A1) ➔</span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Viewport: 3D Canvas + Engineering Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Interactive 3D WebGL Viewer (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <ModelViewer3D key={viewerKey} modelId={model.model_id} height="560px" />

          {/* AI Semantic Vision Recognition Card */}
          {analysis && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-sky-600" />
                  <h3 className="text-sm font-bold text-slate-900">Semantic AI Classification</h3>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-slate-400">Confidence:</span>
                  <span className="text-blue-700 font-semibold">{Math.round(analysis.vision.confidence * 100)}%</span>
                  <span className="text-slate-300">|</span>
                  <span className="text-slate-400">Provider:</span>
                  <span className="text-sky-700 uppercase font-semibold">{analysis.vision.provider_used}</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-700 leading-relaxed font-sans">
                {analysis.vision.visual_description}
              </div>

              {analysis.vision.prominent_features.length > 0 && (
                <div>
                  <div className="text-[11px] font-mono text-slate-500 mb-1.5 uppercase font-medium">DETECTED ANATOMICAL & AESTHETIC FEATURES</div>
                  <div className="flex flex-wrap gap-1.5">
                    {analysis.vision.prominent_features.map((feat, i) => (
                      <span key={i} className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200">
                        {feat}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Technical Geometry & Printability Metrics (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {loading ? (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-10 flex flex-col items-center justify-center gap-3 shadow-xs">
              <div className="w-8 h-8 border-3 border-sky-600/20 border-t-sky-600 rounded-full animate-spin" />
              <div className="text-xs text-slate-500 font-mono">Calculating ray-thickness & overhang matrices...</div>
            </div>
          ) : analysis ? (
            <div className="space-y-4">
              {/* Dimensions & Bounding Envelope */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500 font-semibold">BOUNDING BOX & SCALE</span>
                  <span className={`text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full ${
                    analysis.geometry.fits_bambu_a1
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}>
                    {analysis.geometry.fits_bambu_a1 ? 'FITS BAMBU A1 BED' : 'EXCEEDS BUILD VOLUME'}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">X (WIDTH)</div>
                    <div className="text-sm font-bold text-slate-900 font-mono">{analysis.geometry.dim_x} mm</div>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">Y (DEPTH)</div>
                    <div className="text-sm font-bold text-slate-900 font-mono">{analysis.geometry.dim_y} mm</div>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">Z (HEIGHT)</div>
                    <div className="text-sm font-bold text-slate-900 font-mono">{analysis.geometry.dim_z} mm</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-600 pt-1">
                  <div>Triangles: <span className="text-slate-900 font-semibold">{analysis.geometry.faces.toLocaleString()}</span></div>
                  <div>Watertight: <span className="text-blue-700 font-semibold">{analysis.geometry.is_watertight ? 'Yes (Manifold)' : 'Open Boundaries'}</span></div>
                  <div>Volume: <span className="text-slate-900 font-semibold">{analysis.geometry.volume_cm3} cm³</span></div>
                  <div>Scale: <span className="text-sky-700 font-semibold">{analysis.geometry.scale_category}</span></div>
                </div>
              </div>

              {/* Interactive Scale & Resize Engine */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-mono text-slate-800 font-semibold">
                    <Maximize2 className="w-3.5 h-3.5 text-sky-600" />
                    <span>PRINT SIZE & SCALING ENGINE</span>
                  </div>
                  {scaling && (
                    <span className="text-[11px] font-mono text-sky-600 animate-pulse">
                      Scaling & Re-analyzing...
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 font-sans leading-relaxed">
                  Scale up to fill build volume or scale down for miniatures. Re-evaluates bed fit, wall thickness safety, and split requirements.
                </p>

                {/* Build Volume Fit Alert / Auto-Scale Button */}
                {!analysis.geometry.fits_bambu_a1 && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-amber-800 font-semibold font-mono">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>Exceeds Bambu Lab A1 256mm Build Volume!</span>
                    </div>
                    <p className="text-[11px] text-amber-700 leading-tight">
                      Max dimension is {Math.max(analysis.geometry.dim_x, analysis.geometry.dim_y, analysis.geometry.dim_z)}mm. Click below to automatically scale down to fit the plate safely.
                    </p>
                    <button
                      onClick={() => {
                        const maxD = Math.max(analysis.geometry.dim_x, analysis.geometry.dim_y, analysis.geometry.dim_z);
                        if (maxD > 0) handleScale(240.0 / maxD);
                      }}
                      disabled={scaling}
                      className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-lg transition-colors font-mono shadow-xs"
                    >
                      Fit to Bambu Lab A1 Plate (Auto-Scale to 240mm)
                    </button>
                  </div>
                )}

                {/* Figurine Standard Height Presets */}
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Standard Figurine Scales</span>
                  <div className="grid grid-cols-4 gap-1.5">
                    {[
                      { label: '50mm Mini', z: 50 },
                      { label: '100mm Desk', z: 100 },
                      { label: '150mm Standard', z: 150 },
                      { label: '200mm Display', z: 200 }
                    ].map((p) => (
                      <button
                        key={p.label}
                        onClick={() => handleScale(undefined, p.z)}
                        disabled={scaling}
                        className="px-2 py-1.5 text-xs font-mono font-medium rounded-lg border border-slate-200 bg-slate-50 hover:bg-sky-50 hover:border-sky-300 hover:text-sky-700 transition-colors disabled:opacity-50"
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Percentage Quick Presets */}
                <div className="grid grid-cols-4 gap-1.5 pt-1">
                  {[
                    { label: '50% (Half)', factor: 0.5 },
                    { label: '75% (Small)', factor: 0.75 },
                    { label: '125% (Large)', factor: 1.25 },
                    { label: '150% (Max)', factor: 1.5 }
                  ].map((p) => (
                    <button
                      key={p.label}
                      onClick={() => handleScale(p.factor)}
                      disabled={scaling}
                      className="px-2 py-1.5 text-[11px] font-mono font-medium rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-slate-600 transition-colors disabled:opacity-50"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>

                {/* Custom Height Input */}
                <div className="flex items-center gap-2 pt-1">
                  <div className="relative flex-1">
                    <input
                      type="number"
                      placeholder={`Target Height (current: ${analysis.geometry.dim_z} mm)`}
                      value={customZ}
                      onChange={(e) => setCustomZ(e.target.value)}
                      className="w-full text-xs font-mono px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-sky-500 bg-slate-50/50"
                    />
                    <span className="absolute right-3 top-2 text-[11px] font-mono text-slate-400">mm</span>
                  </div>
                  <button
                    onClick={() => {
                      const val = parseFloat(customZ);
                      if (val > 0) handleScale(undefined, val);
                    }}
                    disabled={scaling || !customZ}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-white transition-colors disabled:opacity-40"
                  >
                    Apply
                  </button>
                </div>

                {/* Next Step Banner */}
                <div className="pt-2 border-t border-slate-100">
                  <button
                    onClick={() => onNavigate('project')}
                    className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <Package className="w-4 h-4" />
                    <span>Proceed to Print Setup & 3MF Packaging ➔</span>
                  </button>
                </div>
              </div>

              {/* Physical Printability Metrics */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
                <span className="text-xs font-mono text-slate-500 font-semibold block">PHYSICAL PRINTABILITY AUDIT</span>

                {/* Wall Thickness */}
                <div className="space-y-1.5 border-b border-slate-100 pb-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-900 font-medium">Wall Thickness (Ray-Sampled)</span>
                    <span className="font-mono text-slate-500">Min: {analysis.thickness.min_thickness_mm} mm</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    Mean: {analysis.thickness.mean_thickness_mm} mm | Max: {analysis.thickness.max_thickness_mm} mm
                  </div>
                  {analysis.thickness.below_nozzle_0_4mm ? (
                    <div className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 p-2 rounded-lg flex items-center gap-1.5 pt-1">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
                      <span>{analysis.thickness.thin_region_count} regions thinner than 0.4mm nozzle diameter.</span>
                    </div>
                  ) : (
                    <div className="text-[11px] text-blue-700 bg-blue-50 border border-blue-200 p-2 rounded-lg flex items-center gap-1.5 pt-1">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-blue-600" />
                      <span>Walls exceed 0.4mm nozzle safe extrusion baseline.</span>
                    </div>
                  )}
                </div>

                {/* Overhangs */}
                <div className="space-y-1.5 border-b border-slate-100 pb-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-900 font-medium">Critical Overhangs (&gt;45°)</span>
                    <span className="font-mono text-amber-700 font-semibold">{analysis.overhang.critical_overhang_area_pct}% area</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    {analysis.overhang.critical_faces_count > 0
                      ? `${analysis.overhang.critical_faces_count.toLocaleString()} downward facing faces require support structure.`
                      : 'Self-supporting geometry: no critical overhangs requiring support detected.'}
                  </div>
                </div>

                {/* Fragility Index */}
                <div className="space-y-1.5 border-b border-slate-100 pb-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-900 font-medium">Structural Fragility Index</span>
                    <span className={`font-mono font-bold ${analysis.fragility.fragility_score > 6 ? 'text-rose-600' : 'text-blue-700'}`}>
                      {analysis.fragility.fragility_score} / 10
                    </span>
                  </div>
                  <div className="text-xs text-slate-500">
                    {analysis.fragility.description}
                  </div>
                </div>

                {/* Floating Islands */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-900 font-medium">Floating Islands & Minima</span>
                    <span className="font-mono text-slate-500">{analysis.islands.floating_island_count} detected</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    {analysis.islands.has_unsupported_minima
                      ? 'Local minima start printing in mid-air; tree supports required.'
                      : 'No unsupported mid-air island seeds detected.'}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {error || 'Analysis could not be completed.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
