import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { TermuxEmulator } from './components/TermuxEmulator';
import { CodeViewer } from './components/CodeViewer';
import { KeyManager } from './components/KeyManager';
import { FileWorkspace } from './components/FileWorkspace';
import { SetupGuide } from './components/SetupGuide';
import { ActiveTab } from './types';
import { Cpu, Terminal, Shield, Code2, Heart } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('emulator');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-mono selection:bg-emerald-500 selection:text-slate-950">
      {/* Navbar Header */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {activeTab === 'emulator' && <TermuxEmulator />}
        {activeTab === 'code' && <CodeViewer />}
        {activeTab === 'keys' && <KeyManager />}
        {activeTab === 'files' && <FileWorkspace />}
        {activeTab === 'setup' && <SetupGuide />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 font-bold">FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE</span>
            <span className="text-slate-600">|</span>
            <span>Termux / Linux Reverse Engineering Engine</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center gap-1 text-slate-500">
              <Shield className="w-3.5 h-3.5 text-cyan-400" />
              <span>HWID Locked Security System</span>
            </span>
            <span className="text-emerald-400 font-bold">PHP & Python Suite</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
