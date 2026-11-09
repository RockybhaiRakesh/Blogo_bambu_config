import React, { useState } from 'react';
import { ModelMetadata, StepId } from '../types';
import { uploadModelFile } from '../services/api';
import {
  Upload,
  FileCheck,
  HardDrive,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

interface UploadScreenProps {
  onModelSelected: (model: ModelMetadata) => void;
  onNavigate: (step: StepId) => void;
}

export const UploadScreen: React.FC<UploadScreenProps> = ({
  onModelSelected,
  onNavigate
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<ModelMetadata | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processUpload(e.target.files[0]);
    }
  };

  const processUpload = async (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.stl', '.obj', '.3mf'].includes(ext)) {
      setError(`Invalid format '${ext}'. Only STL, OBJ and 3MF files are supported.`);
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const res = await uploadModelFile(file);
      setSelectedModel(res.model);
      onModelSelected(res.model);
      setUploading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to upload model.');
      setUploading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Model Ingestion & File Upload</h1>
        <p className="text-sm text-slate-600 mt-1">
          Upload any 3D model (STL, OBJ, or 3MF) to begin automatic size analysis and Bambu Studio 3MF preparation.
        </p>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center transition-all ${
          dragActive
            ? 'border-sky-500 bg-sky-50/50'
            : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/40 shadow-xs'
        }`}
      >
        <input
          type="file"
          id="model-file-input"
          accept=".stl,.obj,.3mf"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="w-16 h-16 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 mb-4 shadow-2xs">
          <Upload className="w-8 h-8" />
        </div>

        <h3 className="text-base font-semibold text-slate-900 mb-1">
          Drag and drop your 3D model here
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mb-5">
          Supports binary & ASCII STL, Wavefront OBJ, and 3D Manufacturing Format (3MF). Maximum size 250 MB.
        </p>

        <label
          htmlFor="model-file-input"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-colors cursor-pointer shadow-xs"
        >
          <HardDrive className="w-4 h-4 text-sky-400" />
          Browse Local Files
        </label>

        {uploading && (
          <div className="mt-6 flex items-center gap-3 text-xs text-sky-600 font-mono">
            <div className="w-4 h-4 border-2 border-sky-600/20 border-t-sky-600 rounded-full animate-spin" />
            Uploading and verifying model integrity...
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Selected Model Confirmation Banner */}
      {selectedModel && (
        <div className="bg-white border border-blue-200 rounded-2xl p-5 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <FileCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs font-mono text-blue-700 font-semibold">READY FOR ANALYSIS</div>
              <div className="text-base font-bold text-slate-900 font-mono">{selectedModel.filename}</div>
              <div className="text-xs text-slate-500 font-mono">
                {(selectedModel.file_size_bytes / (1024 * 1024)).toFixed(2)} MB • Format: {selectedModel.format.toUpperCase()}
              </div>
              <div className="mt-1.5 flex items-center gap-1.5 text-[11px] font-mono text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                <span className="text-slate-400">Stored On Disk:</span>
                <span className="text-slate-800 select-all font-semibold truncate max-w-md sm:max-w-lg" title={selectedModel.file_path}>
                  {selectedModel.file_path}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onNavigate('analyze')}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors shadow-md shadow-blue-600/20 cursor-pointer"
          >
            <span>Proceed to Geometry Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
