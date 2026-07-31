import React, { useState } from 'react';
import { 
  Terminal, 
  Package, 
  Cpu, 
  FileCode, 
  ShieldCheck, 
  HardDrive, 
  Zap, 
  CheckCircle2, 
  Copy, 
  ExternalLink, 
  Code2, 
  Layers,
  Smartphone,
  Info
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'gui' | 'inspector' | 'lua'>('overview');
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  
  // PAK Header Inspector state
  const [pakFileName, setPakFileName] = useState<string>('sample_pubg_game.pak');
  const [pakVersion, setPakVersion] = useState<string>('Version 11 (Encrypted Index)');
  const [pakSize, setPakSize] = useState<string>('3.8 GB');

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(label);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Package className="w-5 h-5 text-slate-950 font-bold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">FeaturesticLeaks PAK Tool</h1>
                <span className="px-2 py-0.5 text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-full">v2.0</span>
              </div>
              <p className="text-xs text-slate-400">Termux-API GUI & Streaming I/O Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <a 
              href="https://t.me/L359D" 
              target="_blank" 
              rel="noreferrer" 
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              <span>Developer: @L359D</span>
              <ExternalLink className="w-3 h-3 text-cyan-400" />
            </a>
            <a 
              href="https://t.me/FeaturesticLeaks" 
              target="_blank" 
              rel="noreferrer" 
              className="text-xs px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <span>Telegram Channel</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav className="bg-slate-900 border-b border-slate-800 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex gap-1 overflow-x-auto py-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === 'overview'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Architecture & Optimizations</span>
          </button>

          <button
            onClick={() => setActiveTab('gui')}
            className={`px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === 'gui'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            <span>Termux-API GUI Launcher</span>
          </button>

          <button
            onClick={() => setActiveTab('inspector')}
            className={`px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === 'inspector'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>PAK Header Inspector</span>
          </button>

          <button
            onClick={() => setActiveTab('lua')}
            className={`px-4 py-2 text-sm font-medium rounded-lg flex items-center gap-2 transition-all whitespace-nowrap ${
              activeTab === 'lua'
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>Lua Compiler Suite</span>
          </button>
        </div>
      </nav>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Hero Card */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
              <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl -z-0 pointer-events-none" />
              <div className="relative z-10 max-w-3xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-semibold border border-cyan-500/20 mb-4">
                  <Zap className="w-3.5 h-3.5" /> High-Performance Engine for 10GB+ Files
                </div>
                <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
                  Zero-Freezing PAK/OBB & Lua Processing Suite
                </h2>
                <p className="text-slate-300 text-base leading-relaxed mb-6">
                  Engineered specifically for Android Termux & Linux environments to handle massive Unreal Engine PAK/OBB archives without memory limits or system crashes.
                </p>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => setActiveTab('gui')}
                    className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl text-sm flex items-center gap-2 transition-colors shadow-lg shadow-cyan-500/20"
                  >
                    <Smartphone className="w-4 h-4" />
                    <span>Termux-API GUI Setup</span>
                  </button>
                  <button
                    onClick={() => copyToClipboard('bash run.sh', 'run')}
                    className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl text-sm flex items-center gap-2 transition-colors border border-slate-700"
                  >
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <span>Copy Launch Command</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Core Optimization Highlights */}
            <div>
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <span>Enterprise Memory & Stability Features</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                    <HardDrive className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-bold text-white mb-1">Streaming I/O Buffer</h4>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Uses memory-mapped (<code className="text-cyan-300">mmap</code>) reads and 64MB streaming chunked writes to process files up to 10GB+ with near-zero heap memory footprint.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-bold text-white mb-1">Resume Checkpointing</h4>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Automatic <code className="text-cyan-300">.progress.json</code> tracking records extracted entries. Interrupted operations resume instantly without duplicate work.
                  </p>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-bold text-white mb-1">Disk Guard & GC</h4>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Pre-checks available storage before unpacking, isolates corrupted entries without crashing, and triggers active garbage collection during long loops.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'gui' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800">
              <div className="flex items-center gap-3 mb-4">
                <Smartphone className="w-6 h-6 text-cyan-400" />
                <div>
                  <h3 className="text-xl font-bold text-white">Termux-API Native GUI Layer</h3>
                  <p className="text-slate-400 text-xs">Visual dialogs for Unpack, Repack, Offsets & Lua tools via Termux-API</p>
                </div>
              </div>

              <p className="text-slate-300 text-sm leading-relaxed mb-6">
                The updated <code className="text-cyan-400 font-mono">run.sh</code> launcher provides a native mobile interface powered by <code className="text-cyan-400 font-mono">termux-dialog</code> and <code className="text-cyan-400 font-mono">termux-toast</code>, featuring storage file selectors, progress toasts, and automatic error popups.
              </p>

              {/* Step by step installation */}
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Step 1: Install Dependencies</span>
                    <button
                      onClick={() => copyToClipboard('pkg update -y && pkg install termux-api jq python -y', 'step1')}
                      className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      {copiedCmd === 'step1' ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-xs font-mono bg-slate-900 p-3 rounded-lg text-slate-200 overflow-x-auto">
                    pkg update -y && pkg install termux-api jq python -y
                  </pre>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Step 2: Launch Termux GUI</span>
                    <button
                      onClick={() => copyToClipboard('bash run.sh', 'step2')}
                      className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      {copiedCmd === 'step2' ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-xs font-mono bg-slate-900 p-3 rounded-lg text-slate-200 overflow-x-auto">
                    bash run.sh
                  </pre>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Step 3: CLI Mode Fallback (Optional)</span>
                    <button
                      onClick={() => copyToClipboard('bash run.sh --cli', 'step3')}
                      className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      {copiedCmd === 'step3' ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-xs font-mono bg-slate-900 p-3 rounded-lg text-slate-200 overflow-x-auto">
                    bash run.sh --cli
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'inspector' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800">
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <Layers className="w-5 h-5 text-cyan-400" />
                <span>PAK File Header & Encryption Inspector</span>
              </h3>
              <p className="text-slate-400 text-xs mb-6">Simulated inspection of Unreal Engine PAK structure</p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Target File</span>
                  <span className="text-sm font-semibold text-white font-mono">{pakFileName}</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Index Format</span>
                  <span className="text-sm font-semibold text-cyan-400 font-mono">{pakVersion}</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-400 block mb-1">Archive Size</span>
                  <span className="text-sm font-semibold text-emerald-400 font-mono">{pakSize}</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2 text-slate-300">
                <div className="flex justify-between border-b border-slate-900 pb-1">
                  <span className="text-slate-500">Magic Header:</span>
                  <span className="text-cyan-400">0x5A6F12E1 (PAK Footer Magic)</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-1">
                  <span className="text-slate-500">Encryption Method:</span>
                  <span className="text-amber-400">AES-256 CBC + RSA Encrypted Index</span>
                </div>
                <div className="flex justify-between border-b border-slate-900 pb-1">
                  <span className="text-slate-500">Compression Method:</span>
                  <span className="text-emerald-400">ZSTD Block Compression (Dictionary Active)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Streaming Read Status:</span>
                  <span className="text-emerald-400">mmap Zero-Copy Active (64MB Chunking)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'lua' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800">
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                <FileCode className="w-5 h-5 text-cyan-400" />
                <span>Lua 5.1 & LuaJIT Compiler Suite</span>
              </h3>
              <p className="text-slate-400 text-xs mb-6">Compile .lua to bytecode (.luac) or inspect decompiled representations</p>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300">
                <div className="text-cyan-400 mb-2">// Sample Lua Script Compilation Command in Termux GUI:</div>
                <pre className="text-slate-200">
{`# Compiles target script into optimized bytecode
luac -o RESULT/script.luac PAK/script.lua

# FeaturesticLeaks automatic decompiler wrapper
python3 FeaturesticLeaks.py --decompile-lua RESULT/script.luac`}
                </pre>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900 py-4 text-center text-xs text-slate-500">
        FeaturesticLeaks PAK Tool v2.0 • Maintained by <span className="text-slate-300 font-semibold">@L359D</span>
      </footer>
    </div>
  );
}
