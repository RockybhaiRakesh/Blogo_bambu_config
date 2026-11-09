import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Copy, Check, RefreshCw, Clock, HardDrive } from 'lucide-react';

interface LogItem {
  filename: string;
  size_bytes: number;
  created_at: string;
  action: string;
}

interface LogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedLogFilename?: string;
}

export const LogsModal: React.FC<LogsModalProps> = ({
  isOpen,
  onClose,
  selectedLogFilename
}) => {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [activeFilename, setActiveFilename] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<string>('');
  const [loadingList, setLoadingList] = useState<boolean>(false);
  const [loadingContent, setLoadingContent] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchList = () => {
    setLoadingList(true);
    fetch('/api/logs')
      .then((res) => res.json())
      .then((data: LogItem[]) => {
        setLogs(data);
        setLoadingList(false);
        if (data.length > 0 && !activeFilename) {
          const target = selectedLogFilename || data[0].filename;
          setActiveFilename(target);
          loadContent(target);
        }
      })
      .catch(() => setLoadingList(false));
  };

  const loadContent = (filename: string) => {
    setActiveFilename(filename);
    setLoadingContent(true);
    fetch(`/api/logs/${encodeURIComponent(filename)}`)
      .then((res) => res.text())
      .then((text) => {
        setLogContent(text);
        setLoadingContent(false);
      })
      .catch(() => {
        setLogContent('Failed to load log file.');
        setLoadingContent(false);
      });
  };

  useEffect(() => {
    if (isOpen) {
      fetchList();
      if (selectedLogFilename) {
        setActiveFilename(selectedLogFilename);
        loadContent(selectedLogFilename);
      }
    }
  }, [isOpen, selectedLogFilename]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(logContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!activeFilename || !logContent) return;
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = activeFilename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">System Execution Logs (.txt)</h3>
              <p className="text-xs text-slate-500 font-mono">
                Persistent event logs stored in <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">/logs</code> directory
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchList}
              title="Refresh logs"
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loadingList ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body - 2 Columns (Left: Log List, Right: Log Content) */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Sidebar: List of Logs */}
          <div className="w-72 sm:w-80 border-r border-slate-100 bg-slate-50/30 flex flex-col overflow-hidden">
            <div className="px-4 py-2.5 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
              <span>Saved Logs ({logs.length})</span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {logs.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  {loadingList ? 'Loading logs...' : 'No logs generated yet.'}
                </div>
              ) : (
                logs.map((item) => {
                  const isActive = activeFilename === item.filename;
                  return (
                    <button
                      key={item.filename}
                      onClick={() => loadContent(item.filename)}
                      className={`w-full text-left p-3 rounded-xl text-xs transition-all flex flex-col gap-1 border ${
                        isActive
                          ? 'bg-sky-50/80 border-sky-200 shadow-xs'
                          : 'bg-white border-slate-200/60 hover:bg-slate-100/60 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className={`font-mono font-medium truncate ${isActive ? 'text-sky-900 font-bold' : 'text-slate-800'}`}>
                          {item.filename}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {item.created_at}
                        </span>
                        <span>{(item.size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Area: Log Content Inspector */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            {activeFilename ? (
              <>
                {/* File Action Bar */}
                <div className="px-6 py-2.5 border-b border-slate-100 flex items-center justify-between bg-white text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">Viewing:</span>
                    <span className="font-semibold text-slate-800">{activeFilename}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-blue-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied' : 'Copy Text'}</span>
                    </button>

                    <button
                      onClick={handleDownload}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-colors shadow-xs"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download .txt</span>
                    </button>
                  </div>
                </div>

                {/* Log Raw Content */}
                <div className="flex-1 p-6 overflow-auto bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed selection:bg-sky-500 selection:text-slate-950">
                  {loadingContent ? (
                    <div className="flex items-center justify-center h-full text-slate-400">
                      Loading file contents...
                    </div>
                  ) : (
                    <pre className="whitespace-pre-wrap font-mono">{logContent}</pre>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
                Select a log file from the left to view contents.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

