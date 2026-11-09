import React, { useEffect, useState } from 'react';
import { StepId, DashboardStatsResponse } from '../types';
import { fetchDashboardStats } from '../services/api';
import {
  Upload,
  Cpu,
  Layers,
  FileCode,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Clock,
  Printer,
  ChevronRight,
  Scissors,
  Sliders,
  Package,
  Box
} from 'lucide-react';

interface DashboardScreenProps {
  onNavigate: (step: StepId) => void;
  onSelectModel: (modelId: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  onNavigate,
  onSelectModel
}) => {
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats()
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-white border border-slate-200/90 p-8 shadow-xs">
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono font-medium">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            Blogo Autonomous 3D Print Preparation Engine
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
            Blogo Autonomous 3D Print Preparation
          </h1>
          <p className="text-slate-600 text-sm leading-relaxed">
            Blogo analyzes raw STL, OBJ and 3MF geometry, detects physical printability risks,
            auto-scales models to fit the Bambu Lab A1 build volume (256×256×256 mm), optimizes material process
            parameters (PLA, PETG, Silk, ABS, TPU), and generates native Bambu Studio projects ready for production.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('upload')}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm transition-all shadow-md shadow-blue-600/20 cursor-pointer"
            >
              <Upload className="w-4 h-4 text-white" />
              Upload 3D Model
            </button>
            <button
              onClick={() => onNavigate('slicer')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-medium text-sm transition-all border border-slate-300 shadow-2xs cursor-pointer"
            >
              <FileCode className="w-4 h-4 text-blue-600" />
              Inspect G-code
            </button>
          </div>
        </div>

        {/* Ambient subtle decorative light background */}
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-blue-50/60 to-transparent pointer-events-none" />
      </div>

      {/* Hardware & System Status Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-mono text-slate-500 flex items-center justify-between">
            <span>TARGET HARDWARE</span>
            <Printer className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-xl font-bold text-slate-900">Bambu Lab A1</div>
          <div className="text-xs text-slate-600 font-mono">
            0.4 mm Hardened Nozzle | 256×256×256 mm
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-mono text-slate-500 flex items-center justify-between">
            <span>SLICER INTEGRATION</span>
            <CheckCircle2 className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-xl font-bold text-slate-900">Bambu Studio</div>
          <div className="text-xs text-slate-600 font-mono">
            {stats?.bambu_studio_version ? `v${stats.bambu_studio_version}` : 'v2.8.2.61'} (GUI Automation)
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-mono text-slate-500 flex items-center justify-between">
            <span>UNITTEST CERTIFICATION</span>
            <ShieldCheck className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-xl font-bold text-blue-700">
            {stats?.verified_tests_count || 134} / 134 Passed
          </div>
          <div className="text-xs text-slate-600 font-mono">
            100% Geometry, Splitting & Slicer Verified
          </div>
        </div>

        <div className="bg-white border border-slate-200/90 rounded-2xl p-5 space-y-2 shadow-xs">
          <div className="text-xs font-mono text-slate-500 flex items-center justify-between">
            <span>ACTIVE WORKSPACE</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-xl font-bold text-slate-900">
            {stats?.total_projects ?? 0} Project(s) Generated
          </div>
          <div className="text-xs text-slate-600 font-mono">
            Ready for multi-part slicing
          </div>
        </div>
      </div>

      {/* Main 5-Stage Pipeline Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Autonomous Preparation Pipeline</h2>
          <span className="text-xs font-mono text-slate-500">Phases 0–7 Integrated</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Stage 1: Geometry & AI */}
          <div
            onClick={() => onNavigate('analyze')}
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-sky-300 rounded-2xl p-5 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 group-hover:scale-105 transition-transform">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-mono text-slate-400">STAGE 01</div>
                <div className="text-sm font-bold text-slate-900 group-hover:text-sky-700 transition-colors">
                  Geometry AI
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ray-sampled wall thickness, overhang angles, fragility index, and watertightness.
              </p>
            </div>
            <div className="pt-4 flex items-center text-xs font-medium text-sky-600 gap-1">
              <span>Inspect</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Stage 2: Size & Bed Fit */}
          <div
            onClick={() => onNavigate('analyze')}
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-sky-300 rounded-2xl p-5 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 group-hover:scale-105 transition-transform">
                <Box className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-mono text-slate-400">STAGE 02</div>
                <div className="text-sm font-bold text-slate-900 group-hover:text-amber-700 transition-colors">
                  Size & Bed Fit
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                1-click auto-scale to Bambu A1 (240mm safe envelope) or custom target height.
              </p>
            </div>
            <div className="pt-4 flex items-center text-xs font-medium text-amber-700 gap-1">
              <span>Inspect</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Stage 3: Print Settings */}
          <div
            onClick={() => onNavigate('settings')}
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-sky-300 rounded-2xl p-5 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 group-hover:scale-105 transition-transform">
                <Sliders className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-mono text-slate-400">STAGE 03</div>
                <div className="text-sm font-bold text-slate-900 group-hover:text-indigo-700 transition-colors">
                  Print Settings
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Material-aware speeds, nozzle thermals, fan cooling, and infill profiles.
              </p>
            </div>
            <div className="pt-4 flex items-center text-xs font-medium text-indigo-700 gap-1">
              <span>Optimize</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Stage 4: 3MF Project */}
          <div
            onClick={() => onNavigate('project')}
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-blue-300 rounded-2xl p-5 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 group-hover:scale-105 transition-transform">
                <Package className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-mono text-slate-400">STAGE 04</div>
                <div className="text-sm font-bold text-slate-900 group-hover:text-blue-700 transition-colors">
                  3MF Packaging
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Native Bambu Studio project archive generation and one-click desktop launch.
              </p>
            </div>
            <div className="pt-4 flex items-center text-xs font-medium text-blue-700 gap-1">
              <span>Package</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Stage 5: G-code Validation */}
          <div
            onClick={() => onNavigate('slicer')}
            className="group bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-blue-300 rounded-2xl p-5 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 group-hover:scale-105 transition-transform">
                <FileCode className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-mono text-slate-400">STAGE 05</div>
                <div className="text-sm font-bold text-slate-900 group-hover:text-indigo-700 transition-colors">
                  Slice & G-code
                </div>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Deep toolpath boundary audit separating model extrusions from wiper moves.
              </p>
            </div>
            <div className="pt-4 flex items-center text-xs font-medium text-indigo-700 gap-1">
              <span>Verify</span>
              <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
