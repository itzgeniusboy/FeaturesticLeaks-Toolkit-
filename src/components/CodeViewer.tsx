import React, { useState } from 'react';
import { Code, Copy, Check, Download, FileText, Search, Info, ShieldCheck, Cpu, Terminal } from 'lucide-react';
import { PYTHON_SCRIPT, PHP_SCRIPT, SETUP_SCRIPT } from '../data/sourceCode';

export const CodeViewer: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<'python' | 'php' | 'setup'>('python');
  const [copied, setCopied] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fileMap = {
    python: {
      name: 'FeaturesticLeaks.py',
      language: 'python',
      code: PYTHON_SCRIPT,
      type: 'Python CLI Application',
      description: 'Main Termux reverse engineering tool using Rich library UI, Android HWID detection, and API client.',
    },
    php: {
      name: 'verify.php',
      language: 'php',
      code: PHP_SCRIPT,
      type: 'PHP Backend Endpoint',
      description: 'PHP REST API handling key verification, hardware ID (HWID) binding, key expiry calculations, and database validation.',
    },
    setup: {
      name: 'setup.sh',
      language: 'bash',
      code: SETUP_SCRIPT,
      type: 'Termux Installation Script',
      description: 'Automated Termux dependency installer (pkg install python php git, pip install rich requests pycryptodome zstandard).',
    },
  };

  const currentFile = fileMap[selectedFile];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentFile.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([currentFile.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFile.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const lines = currentFile.code.split('\n');
  const filteredLines = searchTerm
    ? lines.map((line, idx) => ({ line, num: idx + 1 })).filter(({ line }) => line.toLowerCase().includes(searchTerm.toLowerCase()))
    : lines.map((line, idx) => ({ line, num: idx + 1 }));

  return (
    <div className="space-y-6 font-mono">
      {/* File Selection Tabs Header */}
      <div className="bg-slate-900 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-950 rounded-lg border border-emerald-500/30 text-emerald-400">
              <Code className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-emerald-400">Source Code Studio</h2>
              <p className="text-xs text-slate-400">Inspect, edit, copy, and download production codebase files.</p>
            </div>
          </div>

          {/* Selector Tabs */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setSelectedFile('python')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                selectedFile === 'python'
                  ? 'bg-emerald-600 text-slate-950 shadow-md shadow-emerald-600/30'
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-emerald-500/50'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>FeaturesticLeaks.py</span>
            </button>

            <button
              onClick={() => setSelectedFile('php')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                selectedFile === 'php'
                  ? 'bg-emerald-600 text-slate-950 shadow-md shadow-emerald-600/30'
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-emerald-500/50'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>verify.php</span>
            </button>

            <button
              onClick={() => setSelectedFile('setup')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
                selectedFile === 'setup'
                  ? 'bg-emerald-600 text-slate-950 shadow-md shadow-emerald-600/30'
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-emerald-500/50'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>setup.sh</span>
            </button>
          </div>
        </div>

        {/* File Summary Description */}
        <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="font-bold text-emerald-400">{currentFile.type}: </span>
            <span className="text-slate-300">{currentFile.description}</span>
          </div>
          <span className="text-[11px] text-slate-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">
            {lines.length} Total Lines • UTF-8
          </span>
        </div>
      </div>

      {/* Code Editor Toolbar & Content Window */}
      <div className="bg-slate-950 border border-emerald-900/80 rounded-xl overflow-hidden shadow-2xl">
        {/* Editor Toolbar */}
        <div className="bg-slate-900 border-b border-emerald-900/60 p-3 flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search code..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded pl-8 pr-3 py-1 text-xs text-emerald-300 placeholder-slate-500 focus:outline-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-emerald-900 border border-slate-700 hover:border-emerald-500 text-xs text-emerald-300 font-bold transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy Code'}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs shadow transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download {currentFile.name}</span>
            </button>
          </div>
        </div>

        {/* Code Lines Display */}
        <div className="p-4 overflow-x-auto max-h-[600px] overflow-y-auto font-mono text-xs text-slate-200 leading-relaxed bg-black/90 select-text">
          {filteredLines.map(({ line, num }) => {
            // Basic syntax color styling for readability
            const isComment = line.trim().startsWith('#') || line.trim().startsWith('//') || line.trim().startsWith('/*') || line.trim().startsWith('*');
            const isImport = line.trim().startsWith('import') || line.trim().startsWith('from') || line.trim().startsWith('require') || line.trim().startsWith('use');
            const isDef = line.includes('def ') || line.includes('function ') || line.includes('class ');

            return (
              <div key={num} className="flex hover:bg-slate-900/60 py-0.5 rounded px-1">
                <span className="w-12 shrink-0 text-slate-600 select-none text-right pr-4 text-[11px] font-mono">
                  {num}
                </span>
                <span
                  className={
                    isComment
                      ? 'text-slate-500 italic'
                      : isImport
                      ? 'text-cyan-400 font-bold'
                      : isDef
                      ? 'text-yellow-300 font-bold'
                      : line.includes('SUCCESS') || line.includes('EXPIRED') || line.includes('DEVICE_MISMATCH')
                      ? 'text-emerald-400 font-bold'
                      : 'text-slate-200'
                  }
                >
                  {line || ' '}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Code Architecture Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="bg-slate-900 border border-emerald-900/60 rounded-xl p-4 space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold">
            <ShieldCheck className="w-4 h-4" />
            <span>Android HWID Lock</span>
          </div>
          <p className="text-slate-400">
            Executes <code className="text-emerald-300">getprop ro.serialno</code> via subprocess on Android Termux with fallback to machine-id and MAC hashing.
          </p>
        </div>

        <div className="bg-slate-900 border border-emerald-900/60 rounded-xl p-4 space-y-2">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold">
            <Cpu className="w-4 h-4" />
            <span>Cryptographic Cryptography</span>
          </div>
          <p className="text-slate-400">
            Integrates Zstandard compression and PyCryptodome AES-256 for PAK file container header parsing.
          </p>
        </div>

        <div className="bg-slate-900 border border-emerald-900/60 rounded-xl p-4 space-y-2">
          <div className="flex items-center space-x-2 text-amber-400 font-bold">
            <Info className="w-4 h-4" />
            <span>PHP JSON Database Engine</span>
          </div>
          <p className="text-slate-400">
            Zero-dependency <code className="text-yellow-300">keys_db.json</code> fallback engine for instant server deployment without needing MySQL setup.
          </p>
        </div>
      </div>
    </div>
  );
};
