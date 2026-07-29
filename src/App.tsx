import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { TermuxEmulator } from './components/TermuxEmulator';
import { CodeViewer } from './components/CodeViewer';
import { KeyManager } from './components/KeyManager';
import { FileWorkspace } from './components/FileWorkspace';
import { SetupGuide } from './components/SetupGuide';
import { ActiveTab, ThemeMode } from './types';
import { Cpu, Shield, Sparkles, Terminal, HardDrive, KeyRound } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('emulator');
  const [theme, setTheme] = useState<ThemeMode>('matrix');

  const themeColors = {
    matrix: {
      accentText: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      border: 'border-emerald-500/30',
      footerBorder: 'border-emerald-900/60',
      highlightBadge: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
    },
    cyan: {
      accentText: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      border: 'border-cyan-500/30',
      footerBorder: 'border-cyan-900/60',
      highlightBadge: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/40',
    },
    synthwave: {
      accentText: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      border: 'border-fuchsia-500/30',
      footerBorder: 'border-fuchsia-900/60',
      highlightBadge: 'bg-fuchsia-950/80 text-fuchsia-300 border-fuchsia-500/40',
    },
    solar: {
      accentText: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      border: 'border-amber-500/30',
      footerBorder: 'border-amber-900/60',
      highlightBadge: 'bg-amber-950/80 text-amber-300 border-amber-500/40',
    },
  };

  const currentColors = themeColors[theme];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-mono selection:bg-emerald-500 selection:text-slate-950 transition-colors duration-300">
      {/* Navbar Header with Theme Selector */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} theme={theme} setTheme={setTheme} />

      {/* Main Container Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {activeTab === 'emulator' && <TermuxEmulator theme={theme} />}
        {activeTab === 'code' && <CodeViewer theme={theme} />}
        {activeTab === 'keys' && <KeyManager theme={theme} />}
        {activeTab === 'files' && <FileWorkspace theme={theme} />}
        {activeTab === 'setup' && <SetupGuide theme={theme} />}
      </main>

      {/* Footer Bar */}
      <footer className={`border-t ${currentColors.footerBorder} bg-slate-950/90 py-6 mt-12 transition-colors duration-300`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
            <Cpu className={`w-4 h-4 ${currentColors.accentText}`} />
            <span className={`font-black tracking-wider ${currentColors.accentText} ${currentColors.accentGlow}`}>
              FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE
            </span>
            <span className="text-slate-700">|</span>
            <span className="text-slate-300">Termux & Linux Reverse Engineering Toolkit</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center gap-1 text-slate-400">
              <Shield className={`w-3.5 h-3.5 ${currentColors.accentText}`} />
              <span>Offline Hardware Binding</span>
            </span>
            <span className={`px-2 py-0.5 rounded font-bold border ${currentColors.highlightBadge}`}>
              100% Python & PHP Ready
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
