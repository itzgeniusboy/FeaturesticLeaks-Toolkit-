import React, { useState, useEffect, useRef } from 'react';
import { Terminal, RefreshCw, Key, Shield, Play, Lock, CheckCircle2, AlertTriangle, XCircle, HardDrive, Tv, Sparkles, Send, Command } from 'lucide-react';
import { VerificationResponse, ThemeMode } from '../types';

interface TermuxEmulatorProps {
  theme?: ThemeMode;
}

export const TermuxEmulator: React.FC<TermuxEmulatorProps> = ({ theme = 'matrix' }) => {
  // Theme color map
  const themeStyles = {
    matrix: {
      accent: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      bgGlow: 'box-glow-emerald',
      border: 'border-emerald-500/50',
      borderLight: 'border-emerald-500/30',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500 text-slate-950',
      cardBg: 'bg-emerald-950/40',
      badge: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
      prompt: 'text-emerald-400',
    },
    cyan: {
      accent: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      bgGlow: 'box-glow-cyan',
      border: 'border-cyan-500/50',
      borderLight: 'border-cyan-500/30',
      buttonBg: 'bg-cyan-600 hover:bg-cyan-500 text-slate-950',
      cardBg: 'bg-cyan-950/40',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
      prompt: 'text-cyan-400',
    },
    synthwave: {
      accent: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      bgGlow: 'box-glow-purple',
      border: 'border-fuchsia-500/50',
      borderLight: 'border-fuchsia-500/30',
      buttonBg: 'bg-fuchsia-600 hover:bg-fuchsia-500 text-slate-950',
      cardBg: 'bg-fuchsia-950/40',
      badge: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-500/40',
      prompt: 'text-fuchsia-400',
    },
    solar: {
      accent: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      bgGlow: 'box-glow-amber',
      border: 'border-amber-500/50',
      borderLight: 'border-amber-500/30',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-slate-950',
      cardBg: 'bg-amber-950/40',
      badge: 'bg-amber-950 text-amber-300 border-amber-500/40',
      prompt: 'text-amber-400',
    },
  };

  const style = themeStyles[theme] || themeStyles.matrix;

  // Authentication & Session State
  const [keyInput, setKeyInput] = useState('VIP-AUTO-BYPASS');
  const [hwid, setHwid] = useState('FL-HWID-LOCAL');
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [crtScanlines, setCrtScanlines] = useState(true);
  const [cliInput, setCliInput] = useState('');

  const [authData, setAuthData] = useState<VerificationResponse | null>({
    status: 'SUCCESS',
    message: 'Login Completely Bypassed for Testing',
    timestamp: new Date().toISOString(),
    data: {
      key: 'VIP-AUTO-BYPASS',
      status: 'ACTIVE VIP',
      expiry_date: '31-12-2026',
      days_remaining: 999,
      registered_hwid: 'FL-HWID-LOCAL',
      hwid_matched: true,
    },
  });
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<'main' | 'pak' | 'zip' | 'lua' | 'injector'>('main');

  // Execution State inside Modules
  const [activeTask, setActiveTask] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    `[sys@termux:~]$ python FeaturesticLeaks.py`,
    `[+] 100% Offline VIP Reverse Engineering Toolkit Initialized!`,
    `[+] Rich Console UI Enabled | Zstandard & PyCryptodome Ready`,
    `[+] Type 'help' or click module buttons below to execute tasks.`
  ]);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs, isAuthenticated, currentScreen, activeTask]);

  // Handle Authentication Call - 100% Offline Mode Bypass
  const handleAuthenticate = () => {
    setIsAuthenticating(true);
    const keyToUse = keyInput.trim() || 'VIP-OFFLINE-KEY';
    
    setTerminalLogs((prev) => [
      ...prev,
      `[sys@termux:~]$ python FeaturesticLeaks.py --key ${keyToUse}`,
      `[+] Connecting to local authentication engine...`,
      `[+] Key Verified! HWID: ${hwid}`,
    ]);

    setTimeout(() => {
      const offlineSuccess: VerificationResponse = {
        status: 'SUCCESS',
        message: '100% Offline VIP Access Granted',
        timestamp: new Date().toISOString(),
        data: {
          key: keyToUse,
          status: 'ACTIVE VIP',
          expiry_date: '31-12-2026',
          days_remaining: 999,
          registered_hwid: hwid,
          hwid_matched: true,
        },
      };

      setAuthData(offlineSuccess);
      setIsAuthenticated(true);
      setTerminalLogs((prev) => [
        ...prev,
        `[✔] ACCESS GRANTED! ACTIVE VIP UNLOCKED.`,
        `[✔] License Expiry: 31-12-2026 (999 Days)`,
        `[+] Entering Main Dashboard...`,
      ]);
      setIsAuthenticating(false);
    }, 500);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAuthData(null);
    setCurrentScreen('main');
    setTerminalLogs((prev) => [...prev, `[!] Terminated session. Enter key to re-login.`]);
  };

  const generateRandomHWID = () => {
    const chars = '0123456789ABCDEF';
    let result = '';
    for (let i = 0; i < 16; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setHwid(`FL-HWID-${result}`);
  };

  // Task simulation runner
  const runModuleTask = (taskName: string, duration = 1800, logSuccess: string) => {
    setActiveTask(taskName);
    setProgress(0);
    setTerminalLogs((prev) => [...prev, `[+] Task Started: ${taskName}...`]);

    const interval = setInterval(() => {
      setProgress((old) => {
        if (old >= 100) {
          clearInterval(interval);
          setActiveTask(null);
          setTerminalLogs((prev) => [...prev, `[✔] ${logSuccess}`]);
          return 100;
        }
        return old + 25;
      });
    }, duration / 4);
  };

  // Interactive CLI input handler
  const handleCliSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cliInput.trim()) return;

    const cmd = cliInput.trim().toLowerCase();
    setCliInput('');

    setTerminalLogs((p) => [...p, `[sys@termux:~]$ ${cmd}`]);

    if (cmd === 'clear') {
      setTerminalLogs([]);
      return;
    }
    if (cmd === 'help') {
      setTerminalLogs((p) => [
        ...p,
        `════ Available Commands ════`,
        `  python - Run FeaturesticLeaks.py`,
        `  unpack - Unpack .pak file`,
        `  repack - Repack folder to .pak`,
        `  lua    - Compile / Decompile Lua scripts`,
        `  zip    - Extract & Compress archives`,
        `  hwid   - Inspect hardware ID`,
        `  status - Check server & key status`,
        `  clear  - Clear log output`,
      ]);
      return;
    }
    if (cmd.includes('unpack')) {
      runModuleTask('Unpacking PAK container archive', 1500, 'Files extracted to pak/results/unpack/');
      return;
    }
    if (cmd.includes('repack')) {
      runModuleTask('Repacking pak/results/unpack to PAK', 1500, 'Created pak/results/repack/modded.pak');
      return;
    }
    if (cmd.includes('lua')) {
      runModuleTask('Executing luac compiler & unluac decompiler', 1500, 'Lua bytecode processed successfully!');
      return;
    }
    if (cmd.includes('zip')) {
      runModuleTask('Extracting zip/output archive', 1200, 'Extracted 12 files to zip/extracted/');
      return;
    }
    if (cmd.includes('hwid')) {
      setTerminalLogs((p) => [...p, `[+] Current Device HWID: ${hwid}`]);
      return;
    }
    if (cmd.includes('status')) {
      setTerminalLogs((p) => [...p, `[+] Status: ACTIVE VIP | Days Remaining: 999 | Crypto: AES-256 + zstd`]);
      return;
    }

    setTerminalLogs((p) => [...p, `[!] Command '${cmd}' executed. Type 'help' for command list.`]);
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Top Banner & Presets */}
      <div className={`bg-slate-900/90 border ${style.borderLight} rounded-2xl p-5 shadow-2xl backdrop-blur-lg`}>
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl bg-slate-950 border ${style.border} ${style.accent} shadow-lg`}>
              <Terminal className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className={`text-lg font-black tracking-wide ${style.accent} flex items-center gap-2 ${style.accentGlow}`}>
                Termux CLI Interactive Emulator
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${style.badge}`}>
                  Python 3.11 + Rich UI
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Execute <code className={style.accent}>FeaturesticLeaks.py</code> modules directly in your browser.
              </p>
            </div>
          </div>

          {/* Preset Key Buttons */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-bold">Quick Presets:</span>
            <button
              onClick={() => { setKeyInput('PAK-VIP-9999-ULTIMATE'); setHwid('FL-HWID-3A7F92B0C41E8D5A'); }}
              className={`px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900 font-bold transition shadow-sm`}
            >
              VIP Key
            </button>
            <button
              onClick={() => { setKeyInput('PAK-TEST-2026-KEY1'); setHwid('FL-HWID-3A7F92B0C41E8D5A'); }}
              className="px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 hover:bg-cyan-900 font-bold transition shadow-sm"
            >
              Bound Key
            </button>
            <button
              onClick={() => { setKeyInput('PAK-EXPIRED-KEY-00'); }}
              className="px-3 py-1.5 rounded-lg bg-rose-950/80 border border-rose-500/50 text-rose-300 hover:bg-rose-900 font-bold transition shadow-sm"
            >
              Expired Key
            </button>
          </div>
        </div>

        {/* Input Bar if not logged in */}
        {!isAuthenticated && (
          <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-5">
              <label className={`block text-xs font-bold ${style.accent} mb-1`}>License Key:</label>
              <div className="relative">
                <input
                  type="text"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  placeholder="Enter License Key..."
                  className={`w-full bg-slate-950 border ${style.borderLight} focus:${style.border} rounded-lg px-3 py-2 text-xs ${style.accent} focus:outline-none`}
                />
                <Key className={`w-4 h-4 ${style.accent} absolute right-2.5 top-2.5`} />
              </div>
            </div>

            <div className="md:col-span-5">
              <label className={`block text-xs font-bold ${style.accent} mb-1 flex justify-between`}>
                <span>Hardware ID (HWID):</span>
                <button onClick={generateRandomHWID} className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1">
                  <RefreshCw className="w-2.5 h-2.5" /> Randomize
                </button>
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={hwid}
                  onChange={(e) => setHwid(e.target.value)}
                  className={`w-full bg-slate-950 border ${style.borderLight} focus:${style.border} rounded-lg px-3 py-2 text-xs ${style.accent} focus:outline-none`}
                />
                <Shield className="w-4 h-4 text-cyan-400 absolute right-2.5 top-2.5" />
              </div>
            </div>

            <div className="md:col-span-2 flex items-end">
              <button
                onClick={handleAuthenticate}
                disabled={isAuthenticating}
                className={`w-full ${style.buttonBg} font-extrabold py-2 px-3 rounded-lg shadow-lg flex items-center justify-center gap-2 transition text-xs`}
              >
                {isAuthenticating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <><Play className="w-4 h-4 fill-current" /><span>Authenticate</span></>}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Terminal Screen Window */}
      <div className={`relative bg-black/95 border-2 ${style.border} rounded-2xl shadow-2xl overflow-hidden ${style.bgGlow}`}>
        
        {/* Optional CRT Scanlines Layer */}
        {crtScanlines && <div className="absolute inset-0 crt-scanlines z-10 pointer-events-none rounded-2xl opacity-60" />}

        {/* Titlebar */}
        <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center justify-between z-20 relative">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block shadow-sm shadow-rose-500/50"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block shadow-sm shadow-amber-500/50"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block shadow-sm shadow-emerald-500/50"></span>
            <span className={`text-xs font-black ${style.accent} ml-2 tracking-wider`}>
              termux@android:~ FeaturesticLeaks.py
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <button
              onClick={() => setCrtScanlines(!crtScanlines)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold border ${
                crtScanlines ? 'bg-slate-800 text-emerald-400 border-emerald-500/40' : 'bg-slate-950 text-slate-400 border-slate-800'
              }`}
            >
              <Tv className="w-3 h-3" />
              <span>CRT Overlay: {crtScanlines ? 'ON' : 'OFF'}</span>
            </button>

            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="text-rose-400 hover:text-rose-300 border border-rose-500/40 rounded px-2.5 py-1 text-[10px] font-bold hover:bg-rose-950/60"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Console Content Window */}
        <div className="p-5 min-h-[460px] max-h-[600px] overflow-y-auto space-y-4 text-xs z-20 relative select-text">
          
          {/* ASCII Banner */}
          <div className={`border ${style.border} p-4 rounded-xl ${style.cardBg} text-center space-y-1 shadow-inner`}>
            <pre className={`text-[10px] sm:text-xs font-black leading-none overflow-x-auto whitespace-pre ${style.accent} ${style.accentGlow}`}>
{`███████╗███████╗██████╗ ████████╗██╗██████╗ ███████╗████████╗██╗ ██████╗
██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔══██╗██╔════╝╚══██╔══╝██║██╔════╝
█████╗  █████╗  ██████╔╝   ██║   ██║██████╔╝███████╗   ██║   ██║██║     
██╔══╝  ██╔══╝  ██╔══██╗   ██║   ██║██╔══██╗╚════██║   ██║   ██║██║     
██║     ███████╗██║  ██║   ██║   ██║██║  ██║███████║   ██║   ██║╚██████╗
╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝ ╚═════╝`}
            </pre>
            <div className={`text-yellow-400 font-black tracking-widest text-xs pt-2 ${style.accentGlow}`}>
              ⚡ FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE ⚡
            </div>
            <div className="text-slate-400 text-[11px]">
              Offline Unreal Engine Asset Extractor, Repacker & Lua Bytecode Decompiler
            </div>
          </div>

          {/* License Details Panel */}
          {isAuthenticated && authData && authData.data && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-2`}>
              <div className="text-amber-400 font-extrabold border-b border-slate-800 pb-1.5 flex justify-between items-center text-xs">
                <span className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  <span>OFFLINE LICENSE & DEVICE INFORMATION</span>
                </span>
                <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold border ${style.badge}`}>
                  STATUS: ACTIVE VIP
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400 font-bold">Active Key: </span>
                  <span className={`${style.accent} font-bold`}>{authData.data.key}</span>
                </div>
                <div>
                  <span className="text-cyan-400 font-bold">Expiry Date: </span>
                  <span className="text-cyan-200">{authData.data.expiry_date}</span>
                </div>
                <div>
                  <span className="text-amber-400 font-bold">Days Remaining: </span>
                  <span className="text-amber-300 font-extrabold">{authData.data.days_remaining} Days</span>
                </div>
                <div>
                  <span className="text-slate-400 font-bold">Device HWID: </span>
                  <span className="text-slate-200">{authData.data.registered_hwid}</span>
                </div>
              </div>
            </div>
          )}

          {/* Menu Options Screen */}
          {isAuthenticated && currentScreen === 'main' && (
            <div className={`border ${style.borderLight} rounded-xl bg-slate-950/80 p-4 space-y-3`}>
              <div className="text-yellow-400 font-black text-center border-b border-slate-800 pb-2 tracking-wider">
                ═══ MAIN TOOL MODULES ═══
              </div>

              <div className="grid grid-cols-1 gap-2 text-xs">
                <button
                  onClick={() => setCurrentScreen('pak')}
                  className={`p-3 rounded-lg bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[1] PAK TOOL </span>
                    <span className="text-slate-100 font-bold">- Unpack & Repack PAK Container Archives</span>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('zip')}
                  className={`p-3 rounded-lg bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[2] ZIP TOOL </span>
                    <span className="text-slate-100 font-bold">- ZIP / APK / OBB Archive Utility</span>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('lua')}
                  className={`p-3 rounded-lg bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[3] LUA DECOMPILER </span>
                    <span className="text-slate-100 font-bold">- Compile & Decompile Lua Bytecode Opcodes</span>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('injector')}
                  className={`p-3 rounded-lg bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[4] PAK INJECTOR </span>
                    <span className="text-slate-100 font-bold">- Modded Asset Bytecode Injection</span>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>
              </div>
            </div>
          )}

          {/* Module Screens */}
          {isAuthenticated && currentScreen === 'pak' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[1] PAK ARCHIVE ENGINE</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <button
                  onClick={() => runModuleTask('Unpacking target_game.pak using AES-256 + zstd', 1800, 'Assets extracted to pak/results/unpack/')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900`}
                >
                  Unpack PAK File
                </button>
                <button
                  onClick={() => runModuleTask('Repacking pak/results/unpack folder into PAK', 1800, 'Saved modified PAK to pak/results/repack/modded.pak')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} text-cyan-300 font-extrabold hover:bg-slate-900`}
                >
                  Repack Folder to PAK
                </button>
              </div>
            </div>
          )}

          {isAuthenticated && currentScreen === 'lua' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[3] LUA BYTECODE DECOMPILER ENGINE</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <button
                  onClick={() => runModuleTask('Executing unluac decompiler engine...', 1800, 'Decompiled script saved to lua/decompiled/script.lua')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900`}
                >
                  Decompile .luac to .lua
                </button>
                <button
                  onClick={() => runModuleTask('Executing luac compiler engine...', 1800, 'Compiled script saved to lua/compiled/script.luac')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} text-cyan-300 font-extrabold hover:bg-slate-900`}
                >
                  Compile .lua to Bytecode
                </button>
              </div>
            </div>
          )}

          {/* Active Task Progress */}
          {activeTask && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-3 space-y-2`}>
              <div className={`flex justify-between text-xs font-black ${style.accent}`}>
                <span>⚡ {activeTask}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div
                  className={`h-full rounded-full transition-all duration-200 ${
                    theme === 'matrix'
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-300'
                      : theme === 'cyan'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-400'
                      : theme === 'synthwave'
                      ? 'bg-gradient-to-r from-fuchsia-500 to-purple-400'
                      : 'bg-gradient-to-r from-amber-500 to-yellow-300'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Log Output Stream */}
          <div className="border-t border-slate-800/80 pt-3 space-y-1 text-xs">
            <div className="text-slate-400 font-bold mb-1">TERMINAL LOG OUTPUT:</div>
            {terminalLogs.map((log, index) => (
              <div
                key={index}
                className={
                  log.includes('[✔]')
                    ? 'text-emerald-300 font-extrabold'
                    : log.includes('[!]')
                    ? 'text-rose-400 font-extrabold'
                    : log.includes('[+]')
                    ? style.accent
                    : 'text-slate-300'
                }
              >
                {log}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Command Prompt Form */}
          <form onSubmit={handleCliSubmit} className="pt-3 border-t border-slate-800 flex items-center space-x-2 text-xs">
            <span className={`font-extrabold ${style.prompt}`}>sys@termux:~#</span>
            <input
              type="text"
              value={cliInput}
              onChange={(e) => setCliInput(e.target.value)}
              placeholder="Type 'help', 'unpack', 'repack', 'lua', 'zip', 'clear'..."
              className={`flex-1 bg-transparent text-slate-100 focus:outline-none font-bold placeholder-slate-600`}
            />
            <button type="submit" className={`p-1.5 rounded ${style.buttonBg}`}>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
