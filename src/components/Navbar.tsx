import React from 'react';
import { Terminal, Code, Key, FolderTree, BookOpen, ShieldCheck, Cpu } from 'lucide-react';
import { ActiveTab } from '../types';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'emulator' as ActiveTab, label: 'Termux CLI Emulator', icon: Terminal, badge: 'Live Demo' },
    { id: 'code' as ActiveTab, label: 'Source Code Studio', icon: Code, badge: 'Py & PHP' },
    { id: 'keys' as ActiveTab, label: 'PHP API & Key Manager', icon: Key, badge: 'verify.php' },
    { id: 'files' as ActiveTab, label: 'Virtual File Workspace', icon: FolderTree },
    { id: 'setup' as ActiveTab, label: 'Termux Setup Guide', icon: BookOpen },
  ];

  return (
    <header className="border-b border-emerald-900/60 bg-slate-950/90 backdrop-blur sticky top-0 z-50 shadow-lg shadow-emerald-950/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Tool Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-500/40 text-emerald-400 shadow-sm shadow-emerald-500/20">
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 font-mono">
                  FEATURESTIC LEAKS
                </span>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-emerald-900/80 text-emerald-300 border border-emerald-500/40">
                  PAK TOOL v2.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Termux / Android Reverse Engineering Suite</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 font-mono ${
                    isActive
                      ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20'
                      : 'text-slate-300 hover:text-emerald-400 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Status & Quick Action */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-slate-900 border border-emerald-800/60 text-xs font-mono text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Backend API Online</span>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="lg:hidden flex overflow-x-auto py-2 border-t border-slate-800 space-x-1 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap font-mono ${
                  isActive
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/50'
                    : 'text-slate-300 bg-slate-900'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
