import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, Play, RefreshCw, Send, CornerDownLeft } from 'lucide-react';

export default function App() {
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    'Welcome to Termux!',
    'Docs:       https://termux.dev/docs',
    'Community:  https://termux.dev/community',
    '',
    'Working directory: /sdcard/FeaturesticLeaks',
    '~ $ python3 FeaturesticLeaks.py',
    '',
    '=====================================================================',
    '         🚀 FEATURESTIC LEAKS PAK & LUA MASTER SUITE v2.5 🚀         ',
    '               Developer: @itzraviking | Telegram @L359D             ',
    '=====================================================================',
    ' • OpenCode AI Engine:      https://api.opencode.ai/v1 (Auto-Rotation Active)',
    ' • Telegram Auto-Report:    @L359D Bot linked & active',
    ' • Automatic Bug Repair:    OpenCode AI background auto-recovery enabled',
    '',
    '╔═══════════════════════════════════════════════════════════════════╗',
    '║  [1] AI Watch & Autonomous Modding Assistant 🤖                   ║',
    '║  [2] PAK / OBB Tools (Unpack & Repack) 📦                         ║',
    '║  [3] LUA Tools (Compile, Decompile & Auto 1-Click Workflow) 🌙    ║',
    '║  [4] OpenCode API & Settings 🔑                                   ║',
    '║  [U] Check Auto-Update 🚀                                         ║',
    '║  [0] EXIT ✗                                                       ║',
    '╚═══════════════════════════════════════════════════════════════════╝',
    '',
    '🤖 AI Assistant: Ha bhai! Kya krna h? PAK bnana h, unpack krna h, lua compile krna h, lua pak inject krna h ya fix krna h? Kuch bhi bolo, main direct karke dunga! 🚀',
    ''
  ]);

  const [inputVal, setInputVal] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalOutput]);

  const handleCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const cmd = inputVal.trim();
    setInputVal('');

    setTerminalOutput((prev) => [...prev, `~/FeaturesticLeaks $ ${cmd}`]);

    setTimeout(() => {
      let responses: string[] = [];
      const low = cmd.toLowerCase();

      if (low === '1' || low.includes('watch') || low.includes('assistant')) {
        responses = [
          '🤖 AI MODDING ASSISTANT & COMPANION 🤖',
          'Ha bhai! Workspace input folders scan ho rahe hain...',
          '• INPUT Folder: Ready',
          '• PAK Folder: Ready',
          '• LUA Folder: Ready',
          '• OpenCode AI: Active (Auto-fix background error handling on)',
          'Listening for commands or incoming files...'
        ];
      } else if (low === '2' || low.includes('pak')) {
        responses = [
          '📦 PAK / OBB TOOLS MENU 📦',
          '[1] Unpack PAK/OBB file',
          '[2] Repack folder to PAK',
          '[3] Inject LUA script into PAK',
          '[0] Back to Main Menu'
        ];
      } else if (low === '3' || low.includes('lua')) {
        responses = [
          '🌙 LUA TOOLS MENU 🌙',
          '[1] Compile Lua to Bytecode',
          '[2] Auto-Fix Lua Syntax Errors (OpenCode AI)',
          '[3] 1-Click Auto Lua Workflow',
          '[0] Back to Main Menu'
        ];
      } else if (low === '4' || low.includes('opencode') || low.includes('api')) {
        responses = [
          '🔑 OPENCODE API & TELEGRAM BOT CONFIGURATION 🔑',
          '• OpenCode Base URL: https://api.opencode.ai/v1',
          '• Saved API Keys: Multi-Key Auto Rotation Active',
          '• Telegram Bug Bot: Linked to @L359D',
          '• Developer Tag: @itzraviking'
        ];
      } else if (low.includes('inject')) {
        responses = [
          '🤖 OpenCode AI: Scanning PAK and LUA folders...',
          '💉 Injecting Lua script into ShadowTrackerExtra/Content/Lua...',
          '✅ SUCCESS: Injected PAK saved to /sdcard/FeaturesticLeaks/RESULT/injected_patch.pak! 🚀',
          '(Note: If any bug occurs, OpenCode AI silently fixes it & sends solution report to Telegram!)'
        ];
      } else if (low.includes('unpack') || low.includes('unpak')) {
        responses = [
          '🤖 OpenCode AI: Unpacking PAK archive...',
          '📦 Extraction complete! Unpacked files saved in /sdcard/FeaturesticLeaks/RESULT/ 🚀'
        ];
      } else if (low.includes('repack')) {
        responses = [
          '🤖 OpenCode AI: Repacking unpacked directory...',
          '📦 Repack complete! Repacked PAK file saved in /sdcard/FeaturesticLeaks/RESULT/ 🚀'
        ];
      } else if (low.includes('compile') || low.includes('fix')) {
        responses = [
          '🤖 OpenCode AI: Repairing and compiling Lua 5.1 bytecode...',
          '📜 Complete! Output file written to /sdcard/FeaturesticLeaks/RESULT/ 🚀'
        ];
      } else if (low === 'clear' || low === 'cls') {
        setTerminalOutput(['Welcome to Termux! (FeaturesticLeaks CLI Session Active)', '']);
        return;
      } else {
        responses = [
          `🤖 OpenCode AI: Command '${cmd}' received!`,
          `Processing request through Termux FeaturesticLeaks engine...`,
          `Task completed successfully!`
        ];
      }

      setTerminalOutput((prev) => [...prev, ...responses, '']);
    }, 200);
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono flex flex-col justify-between p-2 md:p-4 select-none">
      {/* Termux Title Header */}
      <div className="bg-slate-900 border-b border-slate-800 px-4 py-2 flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-2">
          <TerminalIcon className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-100">Termux CLI — FeaturesticLeaks.py</span>
        </div>
        <div className="flex items-center space-x-3 text-slate-400 text-[11px]">
          <span className="text-emerald-400">● OpenCode AI Active</span>
          <span>@itzraviking</span>
        </div>
      </div>

      {/* Terminal Screen Body */}
      <div className="flex-1 bg-black p-3 md:p-4 overflow-y-auto font-mono text-xs sm:text-sm leading-relaxed space-y-1">
        {terminalOutput.map((line, idx) => {
          let styleClass = "text-green-400";
          if (line.startsWith('~/FeaturesticLeaks')) styleClass = "text-cyan-300 font-bold";
          else if (line.includes('FEATURESTIC LEAKS') || line.includes('═══')) styleClass = "text-yellow-400 font-bold";
          else if (line.includes('🤖 OpenCode AI') || line.includes('🤖 AI')) styleClass = "text-cyan-400 font-semibold";
          else if (line.includes('ERROR') || line.includes('❌')) styleClass = "text-red-400";
          else if (line.includes('SUCCESS') || line.includes('✅')) styleClass = "text-emerald-400";
          else if (line.startsWith('║') || line.startsWith('╔') || line.startsWith('╚')) styleClass = "text-yellow-300";

          return (
            <div key={idx} className={styleClass}>
              {line}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Termux Input Line */}
      <div className="border-t border-slate-800 pt-2 bg-black">
        <form onSubmit={handleCommand} className="flex items-center space-x-2 px-2 py-1">
          <span className="text-cyan-400 font-bold whitespace-nowrap">$</span>
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Type command or ask OpenCode AI..."
            className="flex-1 bg-transparent text-green-300 font-mono text-sm focus:outline-none placeholder-slate-600"
            autoFocus
          />
          <button type="submit" className="p-1.5 text-cyan-400 hover:text-cyan-300">
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* Termux Keyboard Quick Bar */}
        <div className="flex items-center justify-between text-[10px] text-slate-400 px-2 pt-2 border-t border-slate-900 mt-1">
          <div className="flex space-x-2">
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-slate-300 cursor-pointer">ESC</span>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-slate-300 cursor-pointer">CTRL</span>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-slate-300 cursor-pointer">ALT</span>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-slate-300 cursor-pointer">TAB</span>
          </div>
          <div className="flex space-x-2">
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-cyan-400 cursor-pointer" onClick={() => setInputVal('1')}>[1] AI</span>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-cyan-400 cursor-pointer" onClick={() => setInputVal('2')}>[2] PAK</span>
            <span className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-cyan-400 cursor-pointer" onClick={() => setInputVal('3')}>[3] LUA</span>
          </div>
        </div>
      </div>
    </div>
  );
}
