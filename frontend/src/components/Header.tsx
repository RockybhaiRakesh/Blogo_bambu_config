import React from 'react';
import { StepId } from '../types';
import {
  Layers,
  Upload,
  Cpu,
  Package,
  FileCode,
  ShieldCheck,
  FileText
} from 'lucide-react';

interface HeaderProps {
  currentStep: StepId;
  onNavigate: (step: StepId) => void;
  onOpenLogs?: () => void;
  activeModelName?: string;
  bambuStudioVersion?: string;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onNavigate,
  onOpenLogs,
  activeModelName,
  bambuStudioVersion = 'v2.8.2.61'
}) => {
  const steps: { id: StepId; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <Layers className="w-4 h-4" /> },
    { id: 'upload', label: '1. Upload Model', icon: <Upload className="w-4 h-4" /> },
    { id: 'analyze', label: '2. Size & Geometry', icon: <Cpu className="w-4 h-4" /> },
    { id: 'project', label: '3. Filament & 3MF', icon: <Package className="w-4 h-4" /> },
    { id: 'slicer', label: '4. G-code Verify', icon: <FileCode className="w-4 h-4" /> }
  ];

  return (
    <header className="border-b border-slate-200/80 bg-white/95 backdrop-blur sticky top-0 z-40 shadow-xs">
      {/* Top Brand Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-black text-white text-lg tracking-wider shadow-md shadow-blue-500/20 border border-blue-400/30">
            B
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
                Blogo
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 tracking-normal">AI</span>
              </span>
              <span className="text-[10px] uppercase font-mono font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                Bambu Lab A1
              </span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Autonomous 3D Print Preparation Engine
            </div>
          </div>
        </div>

        {/* System Telemetry & Certification Badges */}
        <div className="flex items-center gap-2.5 text-xs font-mono">
          {activeModelName && (
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50/50 border border-blue-200/80 text-blue-900">
              <span className="text-blue-500">Model:</span>
              <span className="text-blue-700 font-semibold truncate max-w-[140px]">{activeModelName}</span>
            </div>
          )}

          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span>Bambu Studio {bambuStudioVersion}</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            <span>134 Tests Certified</span>
          </div>

          {onOpenLogs && (
            <button
              onClick={onOpenLogs}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 font-medium transition-all shadow-2xs cursor-pointer"
              title="Inspect system .txt logs"
            >
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Logs (.txt)</span>
            </button>
          )}
        </div>
      </div>

      {/* Workflow Navigation Steps */}
      <div className="border-t border-slate-100 bg-slate-50/60">
        <div className="max-w-7xl mx-auto px-4 flex items-center gap-1 overflow-x-auto py-1.5">
          {steps.map((s, idx) => {
            const isActive = currentStep === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onNavigate(s.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-white text-blue-700 border border-blue-300 shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
                }`}
              >
                <span className={`${isActive ? 'text-blue-600' : 'text-slate-400'}`}>
                  {s.icon}
                </span>
                <span>{s.label}</span>
                {idx < steps.length - 1 && (
                  <span className="text-slate-300 ml-1 select-none">/</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
