import React, { useState, useEffect, useRef } from 'react';
import { Terminal, RefreshCw, Key, Shield, Play, Lock, CheckCircle2, AlertTriangle, XCircle, HardDrive } from 'lucide-react';
import { VerificationResponse } from '../types';

export const TermuxEmulator: React.FC = () => {
  // Authentication & Session State - Set default to true for instant zero-prompt testing
  const [keyInput, setKeyInput] = useState('VIP-AUTO-BYPASS');
  const [hwid, setHwid] = useState('LOCAL-DEVICE');
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [authData, setAuthData] = useState<VerificationResponse | null>({
    status: 'SUCCESS',
    message: 'Login Completely Bypassed for Testing',
    timestamp: new Date().toISOString(),
    data: {
      key: 'VIP-AUTO-BYPASS',
      status: 'ACTIVE VIP',
      expiry_date: '31-12-2026',
      days_remaining: 999,
      registered_hwid: 'LOCAL-DEVICE',
      hwid_matched: true,
    },
  });
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<'main' | 'pak' | 'zip' | 'lua' | 'injector'>('main');

  // Interactive Execution State inside Modules
  const [activeTask, setActiveTask] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLogs, isAuthenticated, currentScreen, activeTask]);

  // Handle Authentication Call - 100% Offline Mode Bypass
  const handleAuthenticate = async () => {
    setIsAuthenticating(true);
    const keyToUse = keyInput.trim() || 'VIP-OFFLINE-KEY';
    
    setTerminalLogs((prev) => [
      ...prev,
      `[sys@termux:~]$ python FeaturesticLeaks.py`,
      `[+] Initializing Rich Console Environment (100% Offline Mode)...`,
      `[+] Bypassing network dependencies & online PHP auth...`,
      `[+] Accepting License Key: ${keyToUse}`,
    ]);

    setTimeout(() => {
      const offlineSuccess: VerificationResponse = {
        status: 'SUCCESS',
        message: '100% Offline VIP Bypass Granted',
        timestamp: new Date().toISOString(),
        data: {
          key: keyToUse,
          status: 'ACTIVE VIP',
          expiry_date: '31-12-2026',
          days_remaining: 999,
          registered_hwid: 'LOCAL-DEVICE',
          hwid_matched: true,
        },
      };

      setAuthData(offlineSuccess);
      setIsAuthenticated(true);
      setTerminalLogs((prev) => [
        ...prev,
        `[✔] OFFLINE AUTHENTICATION SUCCESSFUL!`,
        `[✔] Access Status: ACTIVE VIP`,
        `[✔] Active Key: ${keyToUse}`,
        `[✔] Expiry Date: 31-12-2026 (999 Days Remaining)`,
        `[✔] Bound HWID: LOCAL-DEVICE`,
        `[+] Entering FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE Dashboard...`,
      ]);
      setIsAuthenticating(false);
    }, 600);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAuthData(null);
    setCurrentScreen('main');
    setTerminalLogs((prev) => [...prev, `[!] Terminated session and returned to login.`]);
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
  const runModuleTask = (taskName: string, duration = 2000, logSuccess: string) => {
    setActiveTask(taskName);
    setProgress(0);
    setTerminalLogs((prev) => [...prev, `[+] Starting task: ${taskName}...`]);

    const interval = setInterval(() => {
      setProgress((old) => {
        if (old >= 100) {
          clearInterval(interval);
          setActiveTask(null);
          setTerminalLogs((prev) => [...prev, `[✔] ${logSuccess}`]);
          return 100;
        }
        return old + 20;
      });
    }, duration / 5);
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Banner */}
      <div className="bg-slate-900/90 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-xl backdrop-blur">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-950 rounded-lg border border-emerald-500/30 text-emerald-400">
              <Terminal className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold font-mono text-emerald-400 flex items-center gap-2">
                Termux CLI Interactive Emulator
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-900/80 text-emerald-300 font-mono">
                  Python 3.11 + Rich UI
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Simulate <code className="text-emerald-300">FeaturesticLeaks.py</code> execution and test key verification live.
              </p>
            </div>
          </div>

          {/* Quick Preset Keys Picker */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Preset Keys:</span>
            <button
              onClick={() => { setKeyInput('PAK-VIP-9999-ULTIMATE'); setHwid('FL-HWID-3A7F92B0C41E8D5A'); }}
              className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900 transition"
            >
              VIP Key (Valid)
            </button>
            <button
              onClick={() => { setKeyInput('PAK-TEST-2026-KEY1'); setHwid('FL-HWID-3A7F92B0C41E8D5A'); }}
              className="px-2.5 py-1 rounded bg-teal-950/80 border border-teal-500/50 text-teal-300 hover:bg-teal-900 transition"
            >
              Bound Key
            </button>
            <button
              onClick={() => { setKeyInput('PAK-TEST-2026-KEY1'); setHwid('FL-HWID-DIFF-DEVICE-99'); }}
              className="px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/50 text-amber-300 hover:bg-amber-900 transition"
            >
              Mismatch HWID
            </button>
            <button
              onClick={() => { setKeyInput('PAK-EXPIRED-KEY-00'); }}
              className="px-2.5 py-1 rounded bg-rose-950/80 border border-rose-500/50 text-rose-300 hover:bg-rose-900 transition"
            >
              Expired Key
            </button>
          </div>
        </div>

        {/* Input Bar for Authentication if not authenticated */}
        {!isAuthenticated && (
          <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-5">
              <label className="block text-xs font-mono text-emerald-400 mb-1">License Key (key):</label>
              <div className="relative">
                <input
                  type="text"
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  placeholder="Enter License Key..."
                  className="w-full bg-slate-950 border border-emerald-800 focus:border-emerald-400 rounded px-3 py-1.5 text-sm font-mono text-emerald-300 placeholder-slate-600 focus:outline-none"
                />
                <Key className="w-4 h-4 text-emerald-500 absolute right-2.5 top-2.5" />
              </div>
            </div>

            <div className="md:col-span-5">
              <label className="block text-xs font-mono text-emerald-400 mb-1 flex justify-between">
                <span>Hardware ID (hwid):</span>
                <button
                  onClick={generateRandomHWID}
                  className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1"
                >
                  <RefreshCw className="w-2.5 h-2.5" /> Randomize
                </button>
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={hwid}
                  onChange={(e) => setHwid(e.target.value)}
                  className="w-full bg-slate-950 border border-emerald-800 focus:border-emerald-400 rounded px-3 py-1.5 text-sm font-mono text-emerald-300 focus:outline-none"
                />
                <Shield className="w-4 h-4 text-cyan-500 absolute right-2.5 top-2.5" />
              </div>
            </div>

            <div className="md:col-span-2 flex items-end">
              <button
                onClick={handleAuthenticate}
                disabled={isAuthenticating}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold font-mono py-1.5 px-3 rounded shadow-md shadow-emerald-600/30 flex items-center justify-center gap-2 transition duration-150 text-sm disabled:opacity-50"
              >
                {isAuthenticating ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Authenticate</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Live Termux Cyberpunk Terminal Window */}
      <div className="bg-black border-2 border-emerald-500/60 rounded-xl shadow-2xl shadow-emerald-950/50 overflow-hidden font-mono">
        {/* Terminal Title Bar */}
        <div className="bg-slate-900 border-b border-emerald-800/80 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>
            <span className="text-xs font-mono font-bold text-emerald-400 ml-2">
              termux@android:~ FeaturesticLeaks.py
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <span>Python 3.11</span>
            {isAuthenticated && (
              <button
                onClick={handleLogout}
                className="text-rose-400 hover:text-rose-300 border border-rose-500/40 rounded px-2 py-0.5 hover:bg-rose-950/50"
              >
                Logout / Exit
              </button>
            )}
          </div>
        </div>

        {/* Terminal Screen Body */}
        <div className="p-4 sm:p-6 min-h-[480px] max-h-[640px] overflow-y-auto space-y-4 text-emerald-400 text-xs sm:text-sm select-text">
          {/* Header Banner */}
          <div className="border border-emerald-500/60 p-3 sm:p-4 rounded bg-emerald-950/30 text-center space-y-1 shadow-inner shadow-emerald-500/10">
            <pre className="text-[10px] sm:text-xs text-emerald-300 font-extrabold leading-none overflow-x-auto whitespace-pre">
{`███████╗███████╗██████╗ ████████╗██╗██████╗ ███████╗████████╗██╗ ██████╗
██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║██╔══██╗██╔════╝╚══██╔══╝██║██╔════╝
█████╗  █████╗  ██████╔╝   ██║   ██║██████╔╝███████╗   ██║   ██║██║     
██╔══╝  ██╔══╝  ██╔══██╗   ██║   ██║██╔══██╗╚════██║   ██║   ██║██║     
██║     ███████╗██║  ██║   ██║   ██║██║  ██║███████║   ██║   ██║╚██████╗
╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝ ╚═════╝`}
            </pre>
            <div className="text-cyan-300 font-bold tracking-widest text-xs sm:text-sm pt-1">
              ⚡ FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE ⚡
            </div>
            <div className="text-slate-400 text-[11px]">
              Termux Reverse Engineering & Cryptographic Asset Toolkit
            </div>
          </div>

          {/* Account & License Info Panel */}
          {isAuthenticated && authData && authData.data && (
            <div className="border border-emerald-500 rounded bg-slate-950 p-3 sm:p-4 space-y-2">
              <div className="text-amber-400 font-bold border-b border-emerald-900/80 pb-1 flex justify-between items-center">
                <span>🔑 OFFLINE LICENSE & VIP DASHBOARD</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-900 text-emerald-300 border border-emerald-500/40">
                  STATUS: ACTIVE VIP
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-amber-300 font-bold">Active Key: </span>
                  <span className="text-emerald-300">{authData.data.key}</span>
                </div>
                <div>
                  <span className="text-cyan-300 font-bold">Expiry Date: </span>
                  <span className="text-cyan-200">{authData.data.expiry_date}</span>
                </div>
                <div>
                  <span className="text-yellow-300 font-bold">Days Remaining: </span>
                  <span className="text-yellow-200 font-extrabold">{authData.data.days_remaining} Days</span>
                </div>
                <div>
                  <span className="text-slate-400 font-bold">Bound HWID: </span>
                  <span className="text-emerald-400 font-mono">{authData.data.registered_hwid}</span>
                </div>
              </div>
            </div>
          )}

          {/* Unauthenticated Login Prompt */}
          {!isAuthenticated && (
            <div className="border border-amber-500/40 rounded bg-amber-950/20 p-4 space-y-3">
              <div className="flex items-center gap-2 text-amber-400 font-bold">
                <Lock className="w-4 h-4" />
                <span>SYSTEM AUTHENTICATION REQUIRED</span>
              </div>
              <p className="text-slate-300 text-xs">
                Please enter a valid License Key and HWID in the controls above, or pick a preset key to begin.
              </p>
            </div>
          )}

          {/* Interactive Screen: Main Navigation Menu */}
          {isAuthenticated && currentScreen === 'main' && (
            <div className="border border-cyan-500/50 rounded bg-slate-950/80 p-4 space-y-3">
              <div className="text-yellow-400 font-bold text-center border-b border-slate-800 pb-2">
                ═══ MAIN NAVIGATION MENU ═══
              </div>

              <div className="grid grid-cols-1 gap-2 font-mono text-xs">
                <button
                  onClick={() => setCurrentScreen('pak')}
                  className="p-2.5 rounded bg-slate-900 border border-emerald-800 hover:border-emerald-400 hover:bg-emerald-950/60 text-left flex items-center justify-between group transition"
                >
                  <div>
                    <span className="text-yellow-400 font-bold">[1] PAK TOOL </span>
                    <span className="text-white font-semibold">- Extract & Repack PAK Archives</span>
                  </div>
                  <span className="text-xs text-slate-400 group-hover:text-emerald-300">Select &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('zip')}
                  className="p-2.5 rounded bg-slate-900 border border-emerald-800 hover:border-emerald-400 hover:bg-emerald-950/60 text-left flex items-center justify-between group transition"
                >
                  <div>
                    <span className="text-yellow-400 font-bold">[2] ZIP TOOL </span>
                    <span className="text-white font-semibold">- Compress & Decompress Assets</span>
                  </div>
                  <span className="text-xs text-slate-400 group-hover:text-emerald-300">Select &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('lua')}
                  className="p-2.5 rounded bg-slate-900 border border-emerald-800 hover:border-emerald-400 hover:bg-emerald-950/60 text-left flex items-center justify-between group transition"
                >
                  <div>
                    <span className="text-yellow-400 font-bold">[3] LUA TOOL </span>
                    <span className="text-white font-semibold">- Compile & Decompile Lua Scripts</span>
                  </div>
                  <span className="text-xs text-slate-400 group-hover:text-emerald-300">Select &gt;</span>
                </button>

                <button
                  onClick={() => setCurrentScreen('injector')}
                  className="p-2.5 rounded bg-slate-900 border border-emerald-800 hover:border-emerald-400 hover:bg-emerald-950/60 text-left flex items-center justify-between group transition"
                >
                  <div>
                    <span className="text-yellow-400 font-bold">[4] PAK INJECTOR </span>
                    <span className="text-white font-semibold">- Inject Modded Assets</span>
                  </div>
                  <span className="text-xs text-slate-400 group-hover:text-emerald-300">Select &gt;</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="p-2.5 rounded bg-slate-900 border border-rose-800/80 hover:border-rose-400 hover:bg-rose-950/60 text-left flex items-center justify-between text-rose-300 group transition"
                >
                  <div>
                    <span className="text-rose-400 font-bold">[0] EXIT </span>
                    <span className="font-semibold">- Terminate Session & Exit</span>
                  </div>
                  <span className="text-xs text-rose-400">&gt;</span>
                </button>
              </div>
            </div>
          )}

          {/* Module 1: PAK Tool Screen */}
          {isAuthenticated && currentScreen === 'pak' && (
            <div className="border border-cyan-500/60 rounded bg-slate-950 p-4 space-y-3">
              <div className="flex justify-between items-center border-b border-cyan-900/80 pb-2">
                <span className="text-cyan-300 font-bold">[1] PAK ARCHIVE EXTRACTOR & REPACKER</span>
                <button
                  onClick={() => setCurrentScreen('main')}
                  className="text-xs text-amber-400 border border-amber-500/40 rounded px-2 py-0.5 hover:bg-amber-950"
                >
                  &lt; Back to Main Menu
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <p className="text-slate-300">Target Folder: <code className="text-emerald-400">pak/original/</code></p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    onClick={() => runModuleTask('Unpacking PAK file (zstd + AES-256)', 2000, 'Assets extracted to pak/results/unpack/extracted_assets.json')}
                    disabled={activeTask !== null}
                    className="p-2.5 bg-emerald-950 border border-emerald-500 text-emerald-300 rounded font-bold hover:bg-emerald-900 text-center"
                  >
                    Unpack PAK Archive
                  </button>
                  <button
                    onClick={() => runModuleTask('Repacking pak/original to encrypted PAK', 2000, 'Repacked archive saved to pak/results/repack/modded_assets.pak')}
                    disabled={activeTask !== null}
                    className="p-2.5 bg-cyan-950 border border-cyan-500 text-cyan-300 rounded font-bold hover:bg-cyan-900 text-center"
                  >
                    Repack Folder to PAK
                  </button>
                  <button
                    onClick={() => setTerminalLogs((p) => [...p, '[+] PAK Header Magic: 0x5E6F7A8B (UE4 Cryptographic Index)'])}
                    className="p-2.5 bg-slate-900 border border-slate-700 text-yellow-300 rounded font-bold hover:bg-slate-800 text-center"
                  >
                    Inspect PAK Magic
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Module 2: ZIP Tool Screen */}
          {isAuthenticated && currentScreen === 'zip' && (
            <div className="border border-cyan-500/60 rounded bg-slate-950 p-4 space-y-3">
              <div className="flex justify-between items-center border-b border-cyan-900/80 pb-2">
                <span className="text-cyan-300 font-bold">[2] ZIP COMPRESSION & DECOMPRESSION UTILITY</span>
                <button
                  onClick={() => setCurrentScreen('main')}
                  className="text-xs text-amber-400 border border-amber-500/40 rounded px-2 py-0.5 hover:bg-amber-950"
                >
                  &lt; Back to Main Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <button
                  onClick={() => runModuleTask('Extracting ZIP archive...', 1500, 'Files extracted to zip/extracted/')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-emerald-950 border border-emerald-500 text-emerald-300 rounded font-bold hover:bg-emerald-900 text-center"
                >
                  Extract ZIP Archive
                </button>
                <button
                  onClick={() => runModuleTask('Compressing folder to ZIP...', 1500, 'Created zip/output/asset_pack.zip')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-teal-950 border border-teal-500 text-teal-300 rounded font-bold hover:bg-teal-900 text-center"
                >
                  Create ZIP Archive
                </button>
              </div>
            </div>
          )}

          {/* Module 3: LUA Tool Screen */}
          {isAuthenticated && currentScreen === 'lua' && (
            <div className="border border-cyan-500/60 rounded bg-slate-950 p-4 space-y-3">
              <div className="flex justify-between items-center border-b border-cyan-900/80 pb-2">
                <span className="text-cyan-300 font-bold">[3] LUA BYTECODE COMPILER & DECOMPILER</span>
                <button
                  onClick={() => setCurrentScreen('main')}
                  className="text-xs text-amber-400 border border-amber-500/40 rounded px-2 py-0.5 hover:bg-amber-950"
                >
                  &lt; Back to Main Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                <button
                  onClick={() => runModuleTask('Executing luac compiler...', 1800, 'Compiled bytecode saved to lua/compiled/script.luac')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-emerald-950 border border-emerald-500 text-emerald-300 rounded font-bold hover:bg-emerald-900 text-center"
                >
                  Compile Lua (luac)
                </button>
                <button
                  onClick={() => runModuleTask('Executing unluac decompiler...', 1800, 'Decompiled source saved to lua/decompiled/script.lua')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-teal-950 border border-teal-500 text-teal-300 rounded font-bold hover:bg-teal-900 text-center"
                >
                  Decompile Lua (unluac)
                </button>
                <button
                  onClick={() => runModuleTask('XOR String Obfuscation...', 1200, 'Obfuscated strings injected')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-amber-950 border border-amber-500 text-amber-300 rounded font-bold hover:bg-amber-900 text-center"
                >
                  Obfuscate Strings
                </button>
              </div>
            </div>
          )}

          {/* Module 4: PAK Injector Screen */}
          {isAuthenticated && currentScreen === 'injector' && (
            <div className="border border-cyan-500/60 rounded bg-slate-950 p-4 space-y-3">
              <div className="flex justify-between items-center border-b border-cyan-900/80 pb-2">
                <span className="text-cyan-300 font-bold">[4] PAK ASSET INJECTOR MODULE</span>
                <button
                  onClick={() => setCurrentScreen('main')}
                  className="text-xs text-amber-400 border border-amber-500/40 rounded px-2 py-0.5 hover:bg-amber-950"
                >
                  &lt; Back to Main Menu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                <button
                  onClick={() => runModuleTask('Creating Safety Backup...', 1200, 'Backup saved to injector/backup/target_pak.bak')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-emerald-950 border border-emerald-500 text-emerald-300 rounded font-bold hover:bg-emerald-900 text-center"
                >
                  1. Create PAK Backup
                </button>
                <button
                  onClick={() => runModuleTask('Injecting Asset Bytecode...', 2200, 'Modded Bytecode injected! Index offsets recalculated.')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-amber-950 border border-amber-500 text-amber-300 rounded font-bold hover:bg-amber-900 text-center"
                >
                  2. Inject Modded Bytecode
                </button>
                <button
                  onClick={() => runModuleTask('Restoring Backup...', 1000, 'Original PAK restored from backup.')}
                  disabled={activeTask !== null}
                  className="p-2.5 bg-slate-900 border border-slate-700 text-slate-300 rounded font-bold hover:bg-slate-800 text-center"
                >
                  3. Restore Backup
                </button>
              </div>
            </div>
          )}

          {/* Active Task Progress Bar Indicator */}
          {activeTask && (
            <div className="border border-emerald-500/80 rounded bg-slate-950 p-3 space-y-1.5">
              <div className="flex justify-between text-xs text-emerald-300 font-bold">
                <span>⚡ {activeTask}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full transition-all duration-200"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Console Log Buffer */}
          <div className="border-t border-slate-900 pt-3 space-y-1 text-xs">
            <div className="text-slate-400 font-bold mb-1">TERMINAL LOG OUTPUT:</div>
            {terminalLogs.map((log, index) => (
              <div
                key={index}
                className={
                  log.includes('[✔]')
                    ? 'text-emerald-300 font-bold'
                    : log.includes('[✖]') || log.includes('[!]')
                    ? 'text-rose-400 font-bold'
                    : log.includes('[+]')
                    ? 'text-cyan-300'
                    : 'text-slate-300'
                }
              >
                {log}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Command Prompt Line */}
          <div className="pt-2 flex items-center space-x-2 text-xs border-t border-slate-900">
            <span className="text-emerald-400 font-bold">FEATURESTIC@termux:~#</span>
            <span className="w-2 h-4 bg-emerald-400 animate-pulse"></span>
          </div>
        </div>
      </div>
    </div>
  );
};
