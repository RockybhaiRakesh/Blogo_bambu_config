import React, { useState, useEffect } from 'react';
import {
  PrinterProfile,
  FilamentProfile,
  PrintSettingsResponse,
  StepId
} from '../types';
import { fetchPrinters, fetchFilaments, optimizeSettings } from '../services/api';
import {
  Sliders,
  Printer,
  Layers,
  Thermometer,
  Gauge,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Flame,
  Fan,
  Clock,
  Sparkles
} from 'lucide-react';

interface SettingsScreenProps {
  onNavigate: (step: StepId) => void;
  onSettingsReady?: (settings: PrintSettingsResponse) => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  onNavigate,
  onSettingsReady
}) => {
  const [printers, setPrinters] = useState<PrinterProfile[]>([]);
  const [filaments, setFilaments] = useState<FilamentProfile[]>([]);
  const [settings, setSettings] = useState<PrintSettingsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Form selections
  const [selectedPrinter, setSelectedPrinter] = useState<string>('bambu_lab_a1');
  const [selectedFilament, setSelectedFilament] = useState<string>('pla_basic');
  const [objective, setObjective] = useState<string>('balanced_quality');
  const [hasConnectors, setHasConnectors] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([fetchPrinters(), fetchFilaments()])
      .then(([pList, fList]) => {
        setPrinters(pList);
        setFilaments(fList);
        // Compute initial optimized settings
        recalcSettings('bambu_lab_a1', 'pla_basic', 'balanced_quality', true);
      })
      .catch((err) => console.error(err));
  }, []);

  const recalcSettings = (printerId: string, filamentId: string, obj: string, connectors: boolean) => {
    setLoading(true);
    optimizeSettings({
      printer_id: printerId,
      filament_id: filamentId,
      objective: obj,
      has_connectors: connectors
    })
      .then((res) => {
        setSettings(res);
        if (onSettingsReady) onSettingsReady(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  const handlePrinterChange = (id: string) => {
    setSelectedPrinter(id);
    recalcSettings(id, selectedFilament, objective, hasConnectors);
  };

  const handleFilamentChange = (id: string) => {
    setSelectedFilament(id);
    recalcSettings(selectedPrinter, id, objective, hasConnectors);
  };

  const handleObjectiveChange = (obj: string) => {
    setObjective(obj);
    recalcSettings(selectedPrinter, selectedFilament, obj, hasConnectors);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Intelligent Print Settings Optimization</h1>
            <span className="text-xs font-mono font-medium px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
              Phase 5 Engine
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-mono">
            Autonomous material-aware thermal envelopes, kinematics, wall loops, and support offsets
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('project')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors shadow-xs"
          >
            <span>Generate Bambu 3MF Project</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Grid: Form Controls (4 cols) + Process Parameters Dashboard (8 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Machine & Material Selection (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Target Printer Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
            <div className="flex items-center justify-between text-xs font-mono font-semibold text-slate-500 uppercase">
              <span>TARGET 3D PRINTER</span>
              <Printer className="w-4 h-4 text-sky-600" />
            </div>

            <select
              value={selectedPrinter}
              onChange={(e) => handlePrinterChange(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-mono text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs"
            >
              {printers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.manufacturer}) {p.is_default ? '★ Target Baseline' : ''}
                </option>
              ))}
            </select>

            <div className="text-[11px] font-mono text-slate-600 space-y-1 bg-slate-50 p-3 rounded-xl border border-slate-100">
              <div>Build Volume: <span className="text-slate-900 font-semibold">256 × 256 × 256 mm</span></div>
              <div>Nozzle Diameter: <span className="text-slate-900 font-semibold">0.4 mm Baseline</span></div>
              <div>Bed Surface: <span className="text-slate-900 font-semibold">Textured PEI Plate</span></div>
              <div>Kinematics: <span className="text-sky-700 font-semibold">Direct-Drive Active Flow</span></div>
            </div>
          </div>

          {/* Filament Profile Card */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
            <div className="flex items-center justify-between text-xs font-mono font-semibold text-slate-500 uppercase">
              <span>FILAMENT MATERIAL PROFILE</span>
              <Layers className="w-4 h-4 text-amber-600" />
            </div>

            <select
              value={selectedFilament}
              onChange={(e) => handleFilamentChange(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-mono text-slate-800 focus:outline-none focus:border-sky-500 shadow-2xs"
            >
              {filaments.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.brand} {f.material_name} ({f.category.toUpperCase()})
                </option>
              ))}
            </select>

            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-500">Profile Provenance:</span>
              <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold text-[10px]">
                MANUFACTURER_VERIFIED
              </span>
            </div>
          </div>

          {/* Optimization Objective Selector */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
            <span className="text-xs font-mono font-semibold text-slate-500 block uppercase">OPTIMIZATION OBJECTIVE</span>

            <div className="space-y-1.5">
              {[
                { id: 'balanced_quality', name: 'Balanced Quality', desc: 'Optimal trade-off between detail and print duration.' },
                { id: 'max_quality', name: 'Max Detail / Figurines', desc: '0.08mm fine layers, low outer wall speed (40mm/s).' },
                { id: 'fast_print', name: 'High Speed Production', desc: 'Max volumetric speed flow (21mm³/s), 0.24mm layers.' },
                { id: 'max_strength', name: 'Maximum Mechanical Strength', desc: '5 solid walls, 25% gyroid infill, connector lock.' }
              ].map((ob) => (
                <button
                  key={ob.id}
                  type="button"
                  onClick={() => handleObjectiveChange(ob.id)}
                  className={`w-full p-3 rounded-xl border text-left transition-all ${
                    objective === ob.id
                      ? 'border-sky-500 bg-sky-50 text-sky-950 shadow-2xs'
                      : 'border-slate-200 bg-slate-50/50 text-slate-600 hover:border-slate-300 hover:bg-slate-100/50'
                  }`}
                >
                  <div className="text-xs font-bold font-mono">{ob.name}</div>
                  <div className="text-[10px] text-slate-500">{ob.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Computed Process Parameters (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {settings ? (
            <div className="space-y-4">
              {/* Top Estimates Card */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">ESTIMATED TIME</div>
                    <div className="text-lg font-bold text-sky-700 font-mono">
                      ~{(settings.estimated_print_time_mins / 60).toFixed(1)} hrs
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">{Math.round(settings.estimated_print_time_mins)} mins</div>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">ESTIMATED FILAMENT</div>
                    <div className="text-lg font-bold text-amber-700 font-mono">
                      {settings.estimated_filament_grams.toFixed(1)} g
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">Density 1.24 g/cm³</div>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">NOZZLE TEMP</div>
                    <div className="text-lg font-bold text-rose-700 font-mono">
                      {settings.nozzle_temperature}°C
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">Target Bambu Hotend</div>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div className="text-[10px] text-slate-400 font-mono">BED TEMP</div>
                    <div className="text-lg font-bold text-orange-700 font-mono">
                      {settings.bed_temperature}°C
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">Textured PEI Plate</div>
                  </div>
                </div>
              </div>

              {/* Detailed Slicer Parameters Grid */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-4 shadow-xs">
                <span className="text-xs font-mono text-slate-500 font-semibold block uppercase">INJECTED PROCESS PARAMETERS</span>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Layer & Walls */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                    <div className="text-xs font-bold text-slate-900 font-mono flex items-center justify-between">
                      <span>SHELL & PERIMETERS</span>
                      <span className="text-sky-700">{settings.layer_height_mm} mm layer</span>
                    </div>
                    <div className="text-xs font-mono text-slate-600 space-y-1">
                      <div>Initial Layer Height: <span className="text-slate-900 font-semibold">{settings.initial_layer_height_mm} mm</span></div>
                      <div>Wall Loops: <span className="text-blue-700 font-bold">{settings.wall_loops} perimeters</span></div>
                      <div>Wall Generator: <span className="text-slate-900 font-semibold">{settings.wall_generator} (Arachne)</span></div>
                      <div>Top / Bottom Shells: <span className="text-slate-900 font-semibold">{settings.top_shell_layers} top / {settings.bottom_shell_layers} bottom</span></div>
                    </div>
                  </div>

                  {/* Infill */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                    <div className="text-xs font-bold text-slate-900 font-mono flex items-center justify-between">
                      <span>INFILL ARCHITECTURE</span>
                      <span className="text-amber-700">{settings.sparse_infill_density}</span>
                    </div>
                    <div className="text-xs font-mono text-slate-600 space-y-1">
                      <div>Pattern: <span className="text-slate-900 font-semibold uppercase">{settings.sparse_infill_pattern}</span></div>
                      <div>Isotropic Strength: <span className="text-blue-700 font-semibold">High (3D Continuous)</span></div>
                      <div>Infill Speed: <span className="text-slate-900 font-semibold">150 mm/s</span></div>
                      <div>Nozzle Crossings: <span className="text-slate-900 font-semibold">Avoid Crossing Perimeters</span></div>
                    </div>
                  </div>

                  {/* Supports */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                    <div className="text-xs font-bold text-slate-900 font-mono flex items-center justify-between">
                      <span>TREE SUPPORT STRUCTURES</span>
                      <span className="text-blue-700 font-semibold">{settings.enable_support ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    <div className="text-xs font-mono text-slate-600 space-y-1">
                      <div>Support Style: <span className="text-slate-900 font-semibold">{settings.support_style} (Tree Slim)</span></div>
                      <div>Top Z Release Gap: <span className="text-sky-700 font-bold">{settings.support_top_z_gap_mm} mm</span></div>
                      <div>XY Clearance: <span className="text-slate-900 font-semibold">0.60 mm</span></div>
                      <div>Threshold Angle: <span className="text-slate-900 font-semibold">45° Critical Normal</span></div>
                    </div>
                  </div>

                  {/* Speed & Cooling */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 space-y-2">
                    <div className="text-xs font-bold text-slate-900 font-mono flex items-center justify-between">
                      <span>KINEMATICS & COOLING</span>
                      <span className="text-sky-700">Outer: {settings.outer_wall_speed_mm_s} mm/s</span>
                    </div>
                    <div className="text-xs font-mono text-slate-600 space-y-1">
                      <div>Inner Wall Speed: <span className="text-slate-900 font-semibold">{settings.inner_wall_speed_mm_s} mm/s</span></div>
                      <div>Part Cooling Fan: <span className="text-slate-900 font-semibold">80% - 100%</span></div>
                      <div>Brim Adhesion: <span className="text-slate-900 font-semibold">{settings.brim_type} ({settings.brim_width_mm} mm)</span></div>
                      <div>Fan Off Layers: <span className="text-slate-900 font-semibold">Layer 1 (Adhesion)</span></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Engineering Rationale Card */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-3 shadow-xs">
                <span className="text-xs font-mono text-slate-500 font-semibold block uppercase">ALGORITHMIC ENGINEERING RATIONALE</span>
                <div className="space-y-1.5 text-xs text-slate-700 font-mono">
                  {Object.entries(settings.engineering_rationale).map(([key, val]) => (
                    <div key={key} className="flex items-start gap-2">
                      <span className="text-sky-600 font-bold">•</span>
                      <span><span className="text-slate-500 capitalize">{key}:</span> {val}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400">
              Loading settings optimization engine...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
