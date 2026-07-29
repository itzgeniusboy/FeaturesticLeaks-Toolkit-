import React, { useState } from 'react';
import { Code, Copy, Check, Download, FileText, Search, Info, ShieldCheck, Cpu, Terminal, Sparkles, BookOpen, Trash2, FolderCheck } from 'lucide-react';
import { PYTHON_SCRIPT, PHP_SCRIPT, SETUP_SCRIPT, README_MD, HOW_TO_USE_MD, GITIGNORE_CONTENT, CLEAN_REPO_SH } from '../data/sourceCode';
import { ThemeMode } from '../types';

interface CodeViewerProps {
  theme?: ThemeMode;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ theme = 'matrix' }) => {
  const [selectedFile, setSelectedFile] = useState<'python' | 'php' | 'setup' | 'readme' | 'guide' | 'gitignore' | 'clean'>('python');
  const [copied, setCopied] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const themeStyles = {
    matrix: {
      accent: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      border: 'border-emerald-500/40',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500 text-slate-950',
      activeTab: 'bg-emerald-600 text-slate-950 shadow-lg shadow-emerald-600/30 font-black',
      badge: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
    },
    cyan: {
      accent: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      border: 'border-cyan-500/40',
      buttonBg: 'bg-cyan-600 hover:bg-cyan-500 text-slate-950',
      activeTab: 'bg-cyan-600 text-slate-950 shadow-lg shadow-cyan-600/30 font-black',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
    },
    synthwave: {
      accent: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      border: 'border-fuchsia-500/40',
      buttonBg: 'bg-fuchsia-600 hover:bg-fuchsia-500 text-slate-950',
      activeTab: 'bg-fuchsia-600 text-slate-950 shadow-lg shadow-fuchsia-600/30 font-black',
      badge: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-500/40',
    },
    solar: {
      accent: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      border: 'border-amber-500/40',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-slate-950',
      activeTab: 'bg-amber-600 text-slate-950 shadow-lg shadow-amber-600/30 font-black',
      badge: 'bg-amber-950 text-amber-300 border-amber-500/40',
    },
  };

  const style = themeStyles[theme] || themeStyles.matrix;

  const fileMap = {
    python: {
      name: 'FeaturesticLeaks.py',
      language: 'python',
      code: PYTHON_SCRIPT,
      type: 'Python CLI Application',
      description: 'Main Termux reverse engineering tool using Rich UI, Android HWID detection, and offline authentication.',
    },
    php: {
      name: 'verify.php',
      language: 'php',
      code: PHP_SCRIPT,
      type: 'PHP Backend Endpoint',
      description: 'PHP REST API handling key verification, hardware ID (HWID) binding, key expiry calculations, and database validation.',
    },
    setup: {
      name: 'run.sh',
      language: 'bash',
      code: SETUP_SCRIPT,
      type: 'Termux Auto-Launcher Script',
      description: 'Automated launcher script that installs dependencies (pip install rich requests pycryptodome zstandard) and executes FeaturesticLeaks.py.',
    },
    readme: {
      name: 'README.md',
      language: 'markdown',
      code: README_MD,
      type: 'Repository Overview',
      description: 'GitHub repository documentation explaining features, Termux 1-click install, and structure.',
    },
    guide: {
      name: 'HOW_TO_USE.md',
      language: 'markdown',
      code: HOW_TO_USE_MD,
      type: 'Termux Guide Documentation',
      description: 'Comprehensive step-by-step Termux execution and manual installation guide.',
    },
    gitignore: {
      name: '.gitignore',
      language: 'gitignore',
      code: GITIGNORE_CONTENT,
      type: 'Git Exclusions',
      description: 'Rules to ignore temporary, cache, and compiled files when pushing to GitHub.',
    },
    clean: {
      name: 'clean-repo.sh',
      language: 'bash',
      code: CLEAN_REPO_SH,
      type: 'Git Clean & Push Script',
      description: 'Shell command to remove extra web files and push only pure Termux Python/PHP toolkit to GitHub.',
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
      {/* File Selection Header */}
      <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-5 shadow-2xl backdrop-blur-md`}>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className={`p-3 bg-slate-950 rounded-xl border ${style.border} ${style.accent}`}>
              <Code className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className={`text-lg font-black ${style.accent} ${style.accentGlow}`}>Termux Codebase & Git Exporter</h2>
              <p className="text-xs text-slate-400">Inspect, download, or copy all Termux toolkit files and git cleanup scripts.</p>
            </div>
          </div>

          {/* Selector Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setSelectedFile('python')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'python'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>FeaturesticLeaks.py</span>
            </button>

            <button
              onClick={() => setSelectedFile('php')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'php'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>verify.php</span>
            </button>

            <button
              onClick={() => setSelectedFile('setup')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'setup'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>run.sh</span>
            </button>

            <button
              onClick={() => setSelectedFile('readme')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'readme'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>README.md</span>
            </button>

            <button
              onClick={() => setSelectedFile('guide')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'guide'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-amber-400" />
              <span>HOW_TO_USE.md</span>
            </button>

            <button
              onClick={() => setSelectedFile('gitignore')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'gitignore'
                  ? style.activeTab
                  : 'bg-slate-950 text-slate-300 border border-slate-800 hover:border-slate-700'
              }`}
            >
              <FolderCheck className="w-3.5 h-3.5" />
              <span>.gitignore</span>
            </button>

            <button
              onClick={() => setSelectedFile('clean')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ${
                selectedFile === 'clean'
                  ? 'bg-rose-600 text-white font-black shadow-lg shadow-rose-600/30'
                  : 'bg-slate-950 text-rose-300 border border-rose-500/40 hover:border-rose-400'
              }`}
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>clean-repo.sh</span>
            </button>
          </div>
        </div>

        {/* File Description */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className={`font-bold ${style.accent}`}>{currentFile.type}: </span>
            <span className="text-slate-300">{currentFile.description}</span>
          </div>
          <span className={`text-[11px] text-slate-300 px-2.5 py-1 rounded-md border ${style.badge}`}>
            {lines.length} Total Lines • UTF-8
          </span>
        </div>
      </div>

      {/* Editor Toolbar & Code Area */}
      <div className={`bg-slate-950 border ${style.border} rounded-2xl overflow-hidden shadow-2xl`}>
        {/* Editor Bar */}
        <div className="bg-slate-900/90 border-b border-slate-800 p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search code..."
              className={`w-full bg-slate-950 border border-slate-800 focus:${style.border} rounded-lg pl-9 pr-3 py-1.5 text-xs ${style.accent} placeholder-slate-500 focus:outline-none`}
            />
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-bold transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy Code'}</span>
            </button>

            <button
              onClick={handleDownload}
              className={`flex items-center space-x-1.5 px-4 py-1.5 rounded-lg ${style.buttonBg} font-extrabold text-xs shadow-lg transition`}
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download {currentFile.name}</span>
            </button>
          </div>
        </div>

        {/* Code Content */}
        <div className="p-4 overflow-x-auto max-h-[600px] overflow-y-auto font-mono text-xs text-slate-200 leading-relaxed bg-black/95 select-text">
          {filteredLines.map(({ line, num }) => {
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

      {/* Feature Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-4 space-y-2`}>
          <div className={`flex items-center space-x-2 ${style.accent} font-extrabold`}>
            <ShieldCheck className="w-4 h-4" />
            <span>Android HWID Lock</span>
          </div>
          <p className="text-slate-400">
            Executes <code className={style.accent}>getprop ro.serialno</code> on Android Termux with local fallback hashing.
          </p>
        </div>

        <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-4 space-y-2`}>
          <div className="flex items-center space-x-2 text-cyan-400 font-extrabold">
            <Cpu className="w-4 h-4" />
            <span>Zstandard & PyCryptodome</span>
          </div>
          <p className="text-slate-400">
            Integrates zstd decompression and PyCryptodome AES-256 for PAK binary header extraction.
          </p>
        </div>

        <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-4 space-y-2`}>
          <div className="flex items-center space-x-2 text-amber-400 font-extrabold">
            <Info className="w-4 h-4" />
            <span>Zero-Config PHP Engine</span>
          </div>
          <p className="text-slate-400">
            Zero-dependency <code className="text-yellow-300">keys_db.json</code> fallback engine for instant PHP deployment.
          </p>
        </div>
      </div>
    </div>
  );
};
