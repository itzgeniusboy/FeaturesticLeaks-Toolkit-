import React from 'react';
import { Terminal, Code, Key, FolderTree, BookOpen, ShieldCheck, Cpu, Palette, Sparkles } from 'lucide-react';
import { ActiveTab, ThemeMode } from '../types';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, theme, setTheme }) => {
  const navItems = [
    { id: 'emulator' as ActiveTab, label: 'Termux CLI Emulator', icon: Terminal, badge: 'Interactive' },
    { id: 'code' as ActiveTab, label: 'Source Code Studio', icon: Code, badge: 'Py & PHP' },
    { id: 'keys' as ActiveTab, label: 'PHP API & Key Manager', icon: Key, badge: 'verify.php' },
    { id: 'files' as ActiveTab, label: 'Virtual Workspace', icon: FolderTree },
    { id: 'setup' as ActiveTab, label: 'Setup Guide', icon: BookOpen },
  ];

  const themeConfigs = {
    matrix: {
      border: 'border-emerald-500/40',
      bg: 'bg-emerald-950/90',
      text: 'text-emerald-400',
      activeTabBg: 'bg-emerald-950/90 text-emerald-300 border-emerald-500/60 box-glow-emerald',
      brandGradient: 'from-emerald-400 via-teal-300 to-cyan-400',
      badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      accentGlow: 'text-glow-emerald',
    },
    cyan: {
      border: 'border-cyan-500/40',
      bg: 'bg-cyan-950/90',
      text: 'text-cyan-400',
      activeTabBg: 'bg-cyan-950/90 text-cyan-300 border-cyan-500/60 box-glow-cyan',
      brandGradient: 'from-cyan-400 via-sky-300 to-blue-400',
      badgeBg: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      accentGlow: 'text-glow-cyan',
    },
    synthwave: {
      border: 'border-fuchsia-500/40',
      bg: 'bg-fuchsia-950/90',
      text: 'text-fuchsia-400',
      activeTabBg: 'bg-fuchsia-950/90 text-fuchsia-300 border-fuchsia-500/60 box-glow-purple',
      brandGradient: 'from-fuchsia-400 via-purple-300 to-cyan-400',
      badgeBg: 'bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/30',
      accentGlow: 'text-glow-purple',
    },
    solar: {
      border: 'border-amber-500/40',
      bg: 'bg-amber-950/90',
      text: 'text-amber-400',
      activeTabBg: 'bg-amber-950/90 text-amber-300 border-amber-500/60 box-glow-amber',
      brandGradient: 'from-amber-400 via-yellow-300 to-orange-400',
      badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      accentGlow: 'text-glow-amber',
    },
  };

  const currentTheme = themeConfigs[theme];

  return (
    <header className={`border-b ${currentTheme.border} bg-slate-950/90 backdrop-blur-md sticky top-0 z-50 shadow-2xl transition-colors duration-300`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          
          {/* Brand Logo & Title */}
          <div className="flex items-center space-x-3 shrink-0">
            <div className={`p-2 rounded-xl bg-slate-900 border ${currentTheme.border} ${currentTheme.text} shadow-lg transition-all duration-300`}>
              <Cpu className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className={`font-black text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r ${currentTheme.brandGradient} font-mono uppercase ${currentTheme.accentGlow}`}>
                  FEATURESTIC LEAKS
                </span>
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-bold border ${currentTheme.badgeBg} shadow-sm`}>
                  v2.0 ULTIMATE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono hidden sm:block">Termux / Android Asset Reverse Engineering Engine</p>
            </div>
          </div>

          {/* Navigation Tabs (Desktop) */}
          <nav className="hidden xl:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-bold transition-all duration-200 font-mono border ${
                    isActive
                      ? `${currentTheme.activeTabBg} border`
                      : 'border-transparent text-slate-300 hover:text-slate-100 hover:bg-slate-900/80 hover:border-slate-800'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? currentTheme.text : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-extrabold uppercase border ${currentTheme.badgeBg}`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Theme Palette Switcher & Server Status */}
          <div className="flex items-center space-x-3 shrink-0">
            {/* Theme Selector */}
            <div className="flex items-center space-x-1 bg-slate-900/90 p-1 rounded-lg border border-slate-800">
              <Palette className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1 hidden sm:inline" />
              <button
                onClick={() => setTheme('matrix')}
                title="Matrix Emerald Theme"
                className={`w-5 h-5 rounded-md transition-all ${theme === 'matrix' ? 'bg-emerald-500 ring-2 ring-emerald-400 scale-110 shadow-lg shadow-emerald-500/50' : 'bg-emerald-900/80 hover:bg-emerald-600/80'}`}
              />
              <button
                onClick={() => setTheme('cyan')}
                title="Electric Cyan Theme"
                className={`w-5 h-5 rounded-md transition-all ${theme === 'cyan' ? 'bg-cyan-500 ring-2 ring-cyan-400 scale-110 shadow-lg shadow-cyan-500/50' : 'bg-cyan-900/80 hover:bg-cyan-600/80'}`}
              />
              <button
                onClick={() => setTheme('synthwave')}
                title="Synthwave Purple Theme"
                className={`w-5 h-5 rounded-md transition-all ${theme === 'synthwave' ? 'bg-fuchsia-500 ring-2 ring-fuchsia-400 scale-110 shadow-lg shadow-fuchsia-500/50' : 'bg-fuchsia-900/80 hover:bg-fuchsia-600/80'}`}
              />
              <button
                onClick={() => setTheme('solar')}
                title="Solar Gold Theme"
                className={`w-5 h-5 rounded-md transition-all ${theme === 'solar' ? 'bg-amber-500 ring-2 ring-amber-400 scale-110 shadow-lg shadow-amber-500/50' : 'bg-amber-900/80 hover:bg-amber-600/80'}`}
              />
            </div>

            {/* Server Online Pill */}
            <div className={`hidden md:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-slate-900 border ${currentTheme.border} text-xs font-mono text-slate-200 shadow-inner`}>
              <span className={`w-2 h-2 rounded-full ${theme === 'matrix' ? 'bg-emerald-400' : theme === 'cyan' ? 'bg-cyan-400' : theme === 'synthwave' ? 'bg-fuchsia-400' : 'bg-amber-400'} animate-ping`}></span>
              <ShieldCheck className={`w-3.5 h-3.5 ${currentTheme.text}`} />
              <span className="font-bold">Offline VIP Mode Active</span>
            </div>
          </div>
        </div>

        {/* Navigation Bar (Mobile / Tablet medium) */}
        <div className="xl:hidden flex overflow-x-auto py-2.5 border-t border-slate-800/80 space-x-1.5 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap font-mono transition-all border ${
                  isActive
                    ? `${currentTheme.activeTabBg}`
                    : 'text-slate-300 bg-slate-900/90 border-slate-800 hover:border-slate-700'
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
