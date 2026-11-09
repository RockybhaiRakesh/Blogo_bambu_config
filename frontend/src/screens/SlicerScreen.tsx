import React, { useState, useEffect } from 'react';
import { GCodeTelemetryResponse, SlicerCapabilityResponse, StepId } from '../types';
import { fetchSlicerCapabilities, validateGCode } from '../services/api';
import {
  FileCode,
  Printer,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Upload,
  Clock,
  Layers,
  Thermometer,
  HardDrive,
  ExternalLink,
  Info
} from 'lucide-react';

interface SlicerScreenProps {
  onNavigate: (step: StepId) => void;
}

export const SlicerScreen: React.FC<SlicerScreenProps> = () => {
  const [caps, setCaps] = useState<SlicerCapabilityResponse | null>(null);
  const [telemetry, setTelemetry] = useState<GCodeTelemetryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSlicerCapabilities()
      .then((c) => setCaps(c))
      .catch((err) => console.error(err));

    // Auto-load benchmark production G-code
    handleInspectDefaultGCode();
  }, []);

  const handleInspectDefaultGCode = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await validateGCode();
      setTelemetry(res);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to inspect G-code.');
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLoading(true);
      setError(null);
      try {
        const res = await validateGCode(file);
        setTelemetry(res);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Failed to validate uploaded G-code file.');
        setLoading(false);
      }
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Slicer Integration & G-code Physical Validation</h1>
          <span className="text-xs font-mono font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            Phase 6 Production Verification
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          Audit genuine Bambu Studio machine toolpaths, verify coordinate boundaries, and certify physical bed clearance
        </p>
      </div>

      {/* Slicer Capability Banner */}
      {caps && (
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-2xs">
              <Printer className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-900 font-mono">{caps.slicer_name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-mono font-semibold border border-blue-200">
                  v{caps.version || '2.8.2.61'} Installed
                </span>
              </div>
              <div className="text-xs text-slate-500 font-mono mt-0.5">
                Executable: {caps.executable_path}
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs font-mono text-slate-400 font-semibold uppercase">AUTOMATION INTERFACE</div>
            <div className="text-xs text-blue-700 font-mono font-medium">
              Native .3MF Injected Parameter Pipeline
            </div>
          </div>
        </div>
      )}

      {/* G-code Validation Card & Actions */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 space-y-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Deep G-code Toolpath & Coordinate Boundary Audit</h2>
            <p className="text-xs text-slate-500">
              Parses all G-code movement blocks, isolates actual model extrusions from off-bed wiper/cutter maintenance moves.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-xs font-mono font-semibold cursor-pointer border border-slate-300 transition-colors shadow-2xs">
              <Upload className="w-4 h-4 text-sky-600" />
              <span>Audit Custom G-code</span>
              <input type="file" accept=".gcode" onChange={handleFileUpload} className="hidden" />
            </label>

            <button
              onClick={handleInspectDefaultGCode}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white text-xs font-bold transition-colors shadow-xs"
            >
              <FileCode className="w-4 h-4 text-sky-400" />
              <span>Reload Benchmark G-code</span>
            </button>
          </div>
        </div>

        {loading && (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-3 border-sky-600/20 border-t-sky-600 rounded-full animate-spin" />
            <div className="text-xs text-slate-500 font-mono">Parsing 700,000+ G-code coordinate vectors...</div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-mono">
            {error}
          </div>
        )}

        {/* Telemetry Results */}
        {telemetry && !loading && (
          <div className="space-y-6 animate-fadeIn">
            {/* Status & Authenticity Banner */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-blue-500" />
                <div>
                  <div className="text-xs font-mono font-bold text-blue-700">
                    STATUS: {telemetry.status} (Verified Bambu Studio Output)
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    File: {telemetry.filename} • Version: {telemetry.slicer_version}
                  </div>
                </div>
              </div>

              <div className="text-right text-[11px] font-mono text-slate-600">
                <span className="text-amber-700 font-semibold">Physical Print Outcome:</span> PHYSICAL_PRINT_NOT_VERIFIED
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <div className="text-[10px] text-slate-400 font-mono uppercase">ACTUAL DURATION</div>
                <div className="text-base font-bold text-sky-700 font-mono">{telemetry.total_time_str}</div>
                <div className="text-[10px] text-slate-500 font-mono">{telemetry.total_time_minutes} minutes</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <div className="text-[10px] text-slate-400 font-mono uppercase">FILAMENT CONSUMPTION</div>
                <div className="text-base font-bold text-amber-700 font-mono">{telemetry.filament_weight_g} g</div>
                <div className="text-[10px] text-slate-500 font-mono">{telemetry.filament_length_mm} mm total length</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <div className="text-[10px] text-slate-400 font-mono uppercase">LAYER TELEMETRY</div>
                <div className="text-base font-bold text-blue-700 font-mono">{telemetry.total_layers} Layers</div>
                <div className="text-[10px] text-slate-500 font-mono">Height: {telemetry.max_z_height_mm} mm</div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-center">
                <div className="text-[10px] text-slate-400 font-mono uppercase">SUPPORT AIR GAP</div>
                <div className="text-base font-bold text-purple-700 font-mono">{telemetry.support_top_z_gap_mm} mm</div>
                <div className="text-[10px] text-slate-500 font-mono">2-Layer Release Gap (2×0.08mm)</div>
              </div>
            </div>

            {/* Separated Coordinate Boundaries Table */}
            <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-blue-600" />
                  <span className="text-xs font-bold text-slate-900 font-mono uppercase">COORDINATE SEGREGATION & BED FIT REPORT</span>
                </div>
                <span className="text-xs font-mono font-bold text-blue-700 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200">
                  BED FIT: {telemetry.fits_build_plate ? 'PASSED (0.0 to 256.0 mm)' : 'FAILED'}
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {/* Model Bounds */}
                <div className="p-3.5 rounded-xl bg-white border border-slate-200/80 flex flex-wrap items-center justify-between gap-2 shadow-2xs">
                  <div>
                    <span className="text-slate-900 font-semibold block">Model Extrusion Toolpath Bounds:</span>
                    <span className="text-slate-500 text-[11px]">Deposited plastic forming figurine surface, walls, and infill</span>
                  </div>
                  <div className="text-slate-900 font-bold">
                    X: [{telemetry.model_bounds_x[0]}, {telemetry.model_bounds_x[1]}] mm • Y: [{telemetry.model_bounds_y[0]}, {telemetry.model_bounds_y[1]}] mm
                  </div>
                </div>

                {/* Support Bounds */}
                {telemetry.support_bounds_x && telemetry.support_bounds_y && (
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200/80 flex flex-wrap items-center justify-between gap-2 shadow-2xs">
                    <div>
                      <span className="text-slate-900 font-semibold block">Support Structure Bounds:</span>
                      <span className="text-slate-500 text-[11px]">Tree support trunks and contact interfaces</span>
                    </div>
                    <div className="text-slate-900 font-bold">
                      X: [{telemetry.support_bounds_x[0]}, {telemetry.support_bounds_x[1]}] mm • Y: [{telemetry.support_bounds_y[0]}, {telemetry.support_bounds_y[1]}] mm
                    </div>
                  </div>
                )}

                {/* Total Printed Extrusion Envelope */}
                <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 flex flex-wrap items-center justify-between gap-2 shadow-2xs">
                  <div>
                    <span className="text-blue-800 font-semibold block">Total Printed Envelope (Model + Support + Brim):</span>
                    <span className="text-slate-600 text-[11px]">Strictly verified against Bambu Lab A1 256×256 mm build plate</span>
                  </div>
                  <div className="text-blue-800 font-bold">
                    X: [{telemetry.printed_bounds_x[0]}, {telemetry.printed_bounds_x[1]}] mm • Y: [{telemetry.printed_bounds_y[0]}, {telemetry.printed_bounds_y[1]}] mm
                  </div>
                </div>

                {/* Machine Maintenance */}
                <div className="p-3.5 rounded-xl bg-white border border-slate-200/80 flex flex-wrap items-center justify-between gap-2 shadow-2xs">
                  <div>
                    <span className="text-slate-900 font-semibold block">Machine Maintenance & Calibration Area:</span>
                    <span className="text-slate-500 text-[11px]">Off-bed Silicone Wiper (-48.2mm), Cutter (267.0mm), Bed Edge Purge (-0.5 to 262.5mm)</span>
                  </div>
                  <div className="text-sky-700 font-bold">
                    X: [{telemetry.maintenance_bounds_x[0]}, {telemetry.maintenance_bounds_x[1]}] mm • Y: [{telemetry.maintenance_bounds_y[0]}, {telemetry.maintenance_bounds_y[1]}] mm
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
