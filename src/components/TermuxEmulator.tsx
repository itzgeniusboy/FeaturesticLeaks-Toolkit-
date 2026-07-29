import React, { useState, useEffect, useRef } from 'react';
import { Terminal, RefreshCw, Key, Shield, Play, Lock, CheckCircle2, AlertTriangle, XCircle, HardDrive, Tv, Sparkles, Send, Command, Cpu, Download, Copy, Trash2, Eye, Sliders, Zap, FileCode, Layers } from 'lucide-react';
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
  const [hwid, setHwid] = useState('FL-HWID-LOCAL-3A7F');
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [crtScanlines, setCrtScanlines] = useState(true);
  const [fontSize, setFontSize] = useState<'xs' | 'sm' | 'md'>('xs');
  const [cliInput, setCliInput] = useState('');

  // Module Options
  const [aesKey, setAesKey] = useState('0x4F7A9B1C2D3E8E5F0123456789ABCDEF');
  const [ueVersion, setUeVersion] = useState('UE 4.27 / UE 5.0 (v11)');
  const [luaVersion, setLuaVersion] = useState('Lua 5.3 Bytecode');

  const [authData, setAuthData] = useState<VerificationResponse | null>({
    status: 'SUCCESS',
    message: 'Login Completely Bypassed for Testing',
    timestamp: new Date().toISOString(),
    data: {
      key: 'VIP-AUTO-BYPASS',
      status: 'ACTIVE VIP',
      expiry_date: '31-12-2026',
      days_remaining: 999,
      registered_hwid: 'FL-HWID-LOCAL-3A7F',
      hwid_matched: true,
    },
  });

  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<'main' | 'pak' | 'zip' | 'lua' | 'injector' | 'sys'>('main');

  // Execution State inside Modules
  const [activeTask, setActiveTask] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [copiedLogs, setCopiedLogs] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    `[sys@termux:~]$ python FeaturesticLeaks.py`,
    `[+] 100% Offline VIP Reverse Engineering Toolkit Initialized!`,
    `[+] Rich Console UI Enabled | Zstandard & PyCryptodome Ready`,
    `[+] Environment: Termux Android aarch64 (Linux 5.10.177)`,
    `[+] Type 'help' or select options from the interactive terminal menu.`
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
      `[+] Device Hardware ID Verified: ${hwid}`,
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
        `════ Available Termux Commands ════`,
        `  python     - Run FeaturesticLeaks.py main script`,
        `  unpack     - Unpack .pak file (AES-256 + zstd)`,
        `  repack     - Repack folder to .pak archive`,
        `  lua        - Compile / Decompile Lua bytecode`,
        `  zip        - Extract / Compress ZIP, APK, OBB archives`,
        `  inject     - Bytecode asset injector tool`,
        `  hwid       - Print device hardware fingerprint`,
        `  sysinfo    - Display Android kernel & RAM metrics`,
        `  pkg list   - List installed Termux packages`,
        `  status     - Check VIP license status`,
        `  clear      - Clear terminal log output`,
      ]);
      return;
    }
    if (cmd.includes('unpack')) {
      runModuleTask(`Unpacking PAK archive [${ueVersion}] with AES Key`, 1500, 'Assets extracted to pak/results/unpack/');
      return;
    }
    if (cmd.includes('repack')) {
      runModuleTask('Repacking pak/results/unpack to PAK archive', 1500, 'Created pak/results/repack/modded.pak');
      return;
    }
    if (cmd.includes('lua')) {
      runModuleTask(`Executing decompiler engine [${luaVersion}]`, 1500, 'Lua bytecode decompiled successfully!');
      return;
    }
    if (cmd.includes('zip') || cmd.includes('apk')) {
      runModuleTask('Extracting ZIP / APK archive', 1200, 'Extracted 18 files to zip/extracted/');
      return;
    }
    if (cmd.includes('inject')) {
      runModuleTask('Injecting modded bytecode assets into target PAK', 1800, 'Injection complete! Saved to injector/output/modded.pak');
      return;
    }
    if (cmd.includes('hwid')) {
      setTerminalLogs((p) => [...p, `[+] Android Hardware Serial: ${hwid}`]);
      return;
    }
    if (cmd.includes('sysinfo') || cmd.includes('uname')) {
      setTerminalLogs((p) => [
        ...p,
        `[+] OS Kernel: Linux 5.10.177-android12-9-g3a7f92b`,
        `[+] Architecture: aarch64 (ARM64 8-Core @ 2.84 GHz)`,
        `[+] Termux Storage: 118.4 GB Free / 256.0 GB Total`,
        `[+] RAM Usage: 3.2 GB / 12.0 GB (LPDDR5)`,
      ]);
      return;
    }
    if (cmd.includes('pkg')) {
      setTerminalLogs((p) => [
        ...p,
        `[+] python 3.11.8 (installed)`,
        `[+] php 8.2.14 (installed)`,
        `[+] git 2.43.0 (installed)`,
        `[+] zstd 1.5.5 (installed)`,
      ]);
      return;
    }
    if (cmd.includes('status')) {
      setTerminalLogs((p) => [...p, `[+] Status: ACTIVE VIP | Days Remaining: 999 | Crypto Engine: Ready`]);
      return;
    }

    setTerminalLogs((p) => [...p, `[!] Command '${cmd}' executed. Type 'help' for available commands.`]);
  };

  const handleCopyLogs = () => {
    navigator.clipboard.writeText(terminalLogs.join('\n'));
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  const handleDownloadLogs = () => {
    const blob = new Blob([terminalLogs.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `termux_session_${Date.now()}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Quick auxiliary key button handler
  const sendAuxKey = (keyName: string) => {
    if (keyName === 'CLEAR') {
      setTerminalLogs([]);
    } else if (keyName === 'TAB') {
      setCliInput((prev) => prev + '\t');
    } else if (keyName === 'CTRL+C') {
      setTerminalLogs((prev) => [...prev, `[sys@termux:~]$ ^C`, `[!] Interrupted active process.`]);
      setActiveTask(null);
    } else if (keyName === 'UP') {
      setCliInput('python FeaturesticLeaks.py');
    } else {
      setCliInput((prev) => prev + keyName.toLowerCase());
    }
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Top Banner & Quick Presets */}
      <div className={`bg-slate-900/90 border ${style.borderLight} rounded-2xl p-5 shadow-2xl backdrop-blur-lg`}>
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl bg-slate-950 border ${style.border} ${style.accent} shadow-lg`}>
              <Terminal className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className={`text-lg font-black tracking-wide ${style.accent} flex items-center gap-2 ${style.accentGlow}`}>
                Termux CLI Reverse Engineering Emulator
                <span className={`text-[10px] px-2.5 py-0.5 rounded-full border ${style.badge}`}>
                  Python 3.11 + Rich UI
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Execute <code className={style.accent}>FeaturesticLeaks.py</code> modules directly in Android Termux CLI environment.
              </p>
            </div>
          </div>

          {/* Quick Preset Credentials */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-bold">Presets:</span>
            <button
              onClick={() => { setKeyInput('PAK-VIP-9999-ULTIMATE'); setHwid('FL-HWID-3A7F92B0C41E8D5A'); }}
              className="px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900 font-bold transition shadow-sm"
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
        
        {/* CRT Scanlines Overlay */}
        {crtScanlines && <div className="absolute inset-0 crt-scanlines z-10 pointer-events-none rounded-2xl opacity-60" />}

        {/* Titlebar */}
        <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex flex-wrap items-center justify-between gap-2 z-20 relative">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block shadow-sm shadow-rose-500/50"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block shadow-sm shadow-amber-500/50"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block shadow-sm shadow-emerald-500/50"></span>
            <span className={`text-xs font-black ${style.accent} ml-2 tracking-wider`}>
              termux@android:~ FeaturesticLeaks.py
            </span>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            {/* Font Size Toggle */}
            <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 rounded-md p-0.5 text-[10px]">
              <button
                onClick={() => setFontSize('xs')}
                className={`px-2 py-0.5 rounded ${fontSize === 'xs' ? 'bg-slate-800 text-emerald-400 font-bold' : 'text-slate-500'}`}
              >
                Small
              </button>
              <button
                onClick={() => setFontSize('sm')}
                className={`px-2 py-0.5 rounded ${fontSize === 'sm' ? 'bg-slate-800 text-emerald-400 font-bold' : 'text-slate-500'}`}
              >
                Med
              </button>
              <button
                onClick={() => setFontSize('md')}
                className={`px-2 py-0.5 rounded ${fontSize === 'md' ? 'bg-slate-800 text-emerald-400 font-bold' : 'text-slate-500'}`}
              >
                Large
              </button>
            </div>

            {/* CRT Toggle */}
            <button
              onClick={() => setCrtScanlines(!crtScanlines)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold border ${
                crtScanlines ? 'bg-slate-800 text-emerald-400 border-emerald-500/40' : 'bg-slate-950 text-slate-400 border-slate-800'
              }`}
            >
              <Tv className="w-3 h-3" />
              <span>CRT: {crtScanlines ? 'ON' : 'OFF'}</span>
            </button>

            {/* Log Export Controls */}
            <button
              onClick={handleCopyLogs}
              title="Copy Output Logs"
              className="p-1 text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800 rounded-md"
            >
              <Copy className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleDownloadLogs}
              title="Download Log File"
              className="p-1 text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800 rounded-md"
            >
              <Download className="w-3.5 h-3.5" />
            </button>

            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="text-rose-400 hover:text-rose-300 border border-rose-500/40 rounded px-2 py-1 text-[10px] font-bold hover:bg-rose-950/60"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Console Content Window */}
        <div
          className={`p-5 min-h-[480px] max-h-[640px] overflow-y-auto space-y-4 z-20 relative select-text ${
            fontSize === 'xs' ? 'text-xs' : fontSize === 'sm' ? 'text-sm' : 'text-base'
          }`}
        >
          {/* ASCII Banner */}
          <div className={`border ${style.border} p-4 rounded-xl ${style.cardBg} text-center space-y-1 shadow-inner`}>
            <pre className={`text-[9px] sm:text-xs font-black leading-none overflow-x-auto whitespace-pre ${style.accent} ${style.accentGlow}`}>
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
              <div className="text-yellow-400 font-black text-center border-b border-slate-800 pb-2 tracking-wider text-xs">
                ═══ MAIN TERMUX TOOL MODULES ═══
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                <button
                  onClick={() => setCurrentScreen('pak')}
                  className={`p-3 rounded-xl bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[1] PAK TOOL </span>
                    <div className="text-slate-300 text-[11px] mt-0.5">Unpack & Repack PAK Containers (AES-256 + zstd)</div>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('zip')}
                  className={`p-3 rounded-xl bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[2] ZIP / APK TOOL </span>
                    <div className="text-slate-300 text-[11px] mt-0.5">Archive Extraction & OBB Asset Manager</div>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('lua')}
                  className={`p-3 rounded-xl bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[3] LUA DECOMPILER </span>
                    <div className="text-slate-300 text-[11px] mt-0.5">Compile & Decompile Lua 5.1-5.3 Bytecode</div>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('injector')}
                  className={`p-3 rounded-xl bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-amber-400 font-black">[4] PAK INJECTOR </span>
                    <div className="text-slate-300 text-[11px] mt-0.5">Bytecode Asset & Texture Offset Injector</div>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Run &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('sys')}
                  className={`sm:col-span-2 p-3 rounded-xl bg-slate-900 border ${style.borderLight} hover:${style.border} hover:bg-slate-900/90 text-left flex items-center justify-between group transition`}
                >
                  <div>
                    <span className="text-cyan-400 font-black">[5] ANDROID SYSTEM & RAM INSPECTOR </span>
                    <div className="text-slate-300 text-[11px] mt-0.5">View Termux storage, CPU core loads, kernel specs, and prop serials</div>
                  </div>
                  <span className={`text-xs ${style.accent} group-hover:translate-x-1 transition-transform`}>Inspect &gt;</span>
                </button>
              </div>
            </div>
          )}

          {/* PAK Module Configuration */}
          {isAuthenticated && currentScreen === 'pak' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[1] PAK ARCHIVE ENGINE OPTIONS</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back to Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1 font-bold">Unreal Engine Format Version:</label>
                  <select
                    value={ueVersion}
                    onChange={(e) => setUeVersion(e.target.value)}
                    className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-1.5 ${style.accent} font-bold focus:outline-none`}
                  >
                    <option value="UE 4.26 (v10)">UE 4.26 (v10)</option>
                    <option value="UE 4.27 / UE 5.0 (v11)">UE 4.27 / UE 5.0 (v11)</option>
                    <option value="UE 5.1 / UE 5.2 (v12)">UE 5.1 / UE 5.2 (v12)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1 font-bold">AES-256 Encryption Key:</label>
                  <input
                    type="text"
                    value={aesKey}
                    onChange={(e) => setAesKey(e.target.value)}
                    className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-1.5 ${style.accent} font-bold focus:outline-none`}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
                <button
                  onClick={() => runModuleTask(`Unpacking target_game.pak [${ueVersion}] with AES Key`, 1800, 'Assets extracted to pak/results/unpack/')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900 flex items-center justify-center gap-2`}
                >
                  <Zap className="w-4 h-4" />
                  <span>Unpack .PAK File</span>
                </button>

                <button
                  onClick={() => runModuleTask('Repacking pak/results/unpack folder into PAK archive', 1800, 'Saved modified PAK to pak/results/repack/modded.pak')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} text-cyan-300 font-extrabold hover:bg-slate-900 flex items-center justify-center gap-2`}
                >
                  <Layers className="w-4 h-4" />
                  <span>Repack Folder to .PAK</span>
                </button>
              </div>
            </div>
          )}

          {/* LUA Module Configuration */}
          {isAuthenticated && currentScreen === 'lua' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[3] LUA BYTECODE DECOMPILER ENGINE</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back to Menu
                </button>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 text-xs font-bold">Lua Version & Opcode Standard:</label>
                <select
                  value={luaVersion}
                  onChange={(e) => setLuaVersion(e.target.value)}
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-1.5 text-xs ${style.accent} font-bold focus:outline-none`}
                >
                  <option value="Lua 5.1 Bytecode">Lua 5.1 Bytecode (Standard Game Scripts)</option>
                  <option value="Lua 5.2 Bytecode">Lua 5.2 Bytecode</option>
                  <option value="Lua 5.3 Bytecode">Lua 5.3 Bytecode (Modern Engine Opcodes)</option>
                  <option value="LuaJIT 2.1">LuaJIT 2.1 (Just-In-Time Bytecode)</option>
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
                <button
                  onClick={() => runModuleTask(`Executing unluac decompiler engine [${luaVersion}]...`, 1800, 'Decompiled script saved to lua/decompiled/script.lua')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900 flex items-center justify-center gap-2`}
                >
                  <FileCode className="w-4 h-4" />
                  <span>Decompile .luac to .lua</span>
                </button>

                <button
                  onClick={() => runModuleTask(`Executing luac compiler engine [${luaVersion}]...`, 1800, 'Compiled script saved to lua/compiled/script.luac')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} text-cyan-300 font-extrabold hover:bg-slate-900 flex items-center justify-center gap-2`}
                >
                  <Zap className="w-4 h-4" />
                  <span>Compile .lua to Bytecode</span>
                </button>
              </div>
            </div>
          )}

          {/* ZIP Module Configuration */}
          {isAuthenticated && currentScreen === 'zip' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[2] ZIP / APK / OBB ARCHIVE UTILITY</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back to Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <button
                  onClick={() => runModuleTask('Extracting APK & OBB asset contents...', 1500, 'Files extracted to zip/output/extracted/')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900`}
                >
                  Extract APK / OBB Assets
                </button>
                <button
                  onClick={() => runModuleTask('Compressing modified files to zip archive...', 1500, 'Compressed archive saved to zip/output/modded_assets.zip')}
                  disabled={activeTask !== null}
                  className={`p-3 rounded-lg border ${style.border} ${style.cardBg} text-cyan-300 font-extrabold hover:bg-slate-900`}
                >
                  Compress Folder to ZIP
                </button>
              </div>
            </div>
          )}

          {/* Injector Module Configuration */}
          {isAuthenticated && currentScreen === 'injector' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[4] PAK BYTECODE ASSET INJECTOR</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back to Menu
                </button>
              </div>

              <p className="text-xs text-slate-300">
                Inject modded textures (.tga/.png) or modified bytecode directly into target PAK container headers with offset verification.
              </p>

              <button
                onClick={() => runModuleTask('Injecting custom bytecode into target PAK header...', 1800, 'Injection successful! Modified file saved to injector/output/injected.pak')}
                disabled={activeTask !== null}
                className={`w-full p-3 rounded-lg border ${style.border} ${style.cardBg} ${style.accent} font-extrabold hover:bg-slate-900 flex items-center justify-center gap-2 text-xs`}
              >
                <Zap className="w-4 h-4" />
                <span>Execute Asset Injection Process</span>
              </button>
            </div>
          )}

          {/* System Inspector Screen */}
          {isAuthenticated && currentScreen === 'sys' && (
            <div className={`border ${style.border} rounded-xl bg-slate-950 p-4 space-y-3`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className={`font-black ${style.accent}`}>[5] ANDROID TERMUX SYSTEM SPECS</span>
                <button onClick={() => setCurrentScreen('main')} className="text-xs text-amber-400 border border-amber-500/40 rounded px-2.5 py-1 hover:bg-amber-950">
                  &lt; Back to Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-bold mb-1">Android OS Model:</div>
                  <div className="text-cyan-300 font-mono font-bold">Xiaomi Poco F5 Pro (Android 13)</div>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-bold mb-1">Architecture:</div>
                  <div className="text-emerald-400 font-mono font-bold">aarch64 (Snapdragon 8+ Gen 1)</div>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-bold mb-1">Termux Storage (/sdcard/):</div>
                  <div className="text-amber-300 font-mono font-bold">118.4 GB Free / 256.0 GB Total</div>
                </div>
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                  <div className="text-slate-400 font-bold mb-1">Device Hardware Serial:</div>
                  <div className="text-slate-200 font-mono font-bold">{hwid}</div>
                </div>
              </div>
            </div>
          )}

          {/* Active Task Progress Bar */}
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
          <div className="border-t border-slate-800/80 pt-3 space-y-1">
            <div className="text-slate-400 font-bold mb-1 text-xs">TERMINAL LOG OUTPUT:</div>
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

          {/* Termux On-Screen Auxiliary Keys Row */}
          <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-1 text-[11px] font-bold">
            <span className="text-slate-500 text-[10px] self-center mr-1">Termux Keys:</span>
            {['ESC', 'TAB', 'CTRL+C', 'UP', 'unpack', 'repack', 'lua', 'hwid', 'CLEAR'].map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => sendAuxKey(key)}
                className="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 active:scale-95 transition"
              >
                {key}
              </button>
            ))}
          </div>

          {/* Command Prompt Input */}
          <form onSubmit={handleCliSubmit} className="pt-3 border-t border-slate-800 flex items-center space-x-2 text-xs">
            <span className={`font-extrabold ${style.prompt}`}>sys@termux:~#</span>
            <input
              type="text"
              value={cliInput}
              onChange={(e) => setCliInput(e.target.value)}
              placeholder="Type 'help', 'unpack', 'repack', 'lua', 'zip', 'sysinfo', 'clear'..."
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
