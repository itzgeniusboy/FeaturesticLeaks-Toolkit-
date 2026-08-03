import React, { useState } from 'react';
import { 
  Package, 
  Code2, 
  Bot, 
  Terminal, 
  Settings, 
  FolderOpen, 
  Play, 
  FileText, 
  Zap, 
  ShieldAlert, 
  HelpCircle,
  RefreshCw,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'pak' | 'lua' | 'ai' | 'logs'>('overview');
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([
    { sender: 'ai', text: 'Hii buddy! Welcome to Featurestic Leaks AI Assistant. Aaj kya modding ya leak karni hai?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('P1');
  const [logOutput, setLogOutput] = useState<string[]>([
    '[INIT] Featurestic Leaks PAK Tool v2.5 initialized.',
    '[INFO] Workspace initialized at /sdcard/FeaturesticLeaks',
    '[READY] Select an action to begin.'
  ]);

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput;
    setChatMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setChatInput('');

    setTimeout(() => {
      let reply = "Hii brother! Main aapki modding queries me help karne ke liye ready hu.";
      const lower = userText.toLowerCase();
      if (lower.includes('pak') || lower.includes('unpack')) {
        reply = "📦 PAK Unpack karne ke liye: Select PAK Tool tab -> Select Input File -> Click 'Start Unpack'. Files /sdcard/FeaturesticLeaks/UNPACK me save hongi!";
      } else if (lower.includes('lua') || lower.includes('compile')) {
        reply = "📜 Lua Script compile karne ke liye: Lua Tool tab me jaao. Direct bytecode generation and Lua 5.1 syntax repair supported hai!";
      } else if (lower.includes('preset') || lower.includes('path')) {
        reply = "🎯 PUBG/BGMI modding ke liye Preset P1 (Content/Lua/GameLua/Mod/BRMod/Gameplay/Core) select karein!";
      }

      setChatMessages((prev) => [...prev, { sender: 'ai', text: reply }]);
    }, 600);
  };

  const triggerAction = (actionName: string) => {
    setLogOutput((prev) => [
      ...prev,
      `[EXEC] Running ${actionName}...`,
      `[SUCCESS] ${actionName} completed successfully.`
    ]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-lg shadow-lg shadow-cyan-500/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              Featurestic Leaks
            </h1>
            <p className="text-xs text-slate-400">PAK/OBB & Lua Master Suite v2.5</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="px-3 py-1.5 bg-slate-800 rounded-md border border-slate-700 flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-300 font-mono">CLI & GUI Sync</span>
          </div>
          <button 
            onClick={() => triggerAction('Auto-Update Check')} 
            className="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500/30 rounded-md flex items-center space-x-1.5 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Auto-Update</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4 flex flex-col justify-between">
          <div className="space-y-1">
            <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Navigation
            </div>

            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'overview'
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab('pak')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'pak'
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Package className="w-4 h-4" />
              <span>PAK / OBB Tool</span>
            </button>

            <button
              onClick={() => setActiveTab('lua')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'lua'
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Code2 className="w-4 h-4" />
              <span>Lua Compiler & Repair</span>
            </button>

            <button
              onClick={() => setActiveTab('ai')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'ai'
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>AI Companion</span>
            </button>

            <button
              onClick={() => setActiveTab('logs')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'logs'
                  ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>System Console</span>
            </button>
          </div>

          <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
            <div className="text-xs text-slate-400 font-medium">Developer</div>
            <div className="text-sm font-semibold text-cyan-400">@L359D</div>
            <div className="text-xs text-slate-500 mt-1">t.me/FeaturesticLeaks</div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 p-6 overflow-y-auto bg-slate-950">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Top Banner */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-cyan-500/20 shadow-xl relative overflow-hidden">
                <div className="relative z-10 max-w-2xl">
                  <span className="px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs font-semibold rounded-full uppercase tracking-wider">
                    Termux & Linux Suite
                  </span>
                  <h2 className="text-2xl font-bold mt-3 text-white">
                    High-Performance Game Asset & Script Engine
                  </h2>
                  <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                    Unpack, edit, compile and repack Tencent PAK/OBB archives with automated offset detection and Lua 5.1 syntax repair.
                  </p>

                  <div className="flex items-center space-x-3 mt-5">
                    <button 
                      onClick={() => setActiveTab('pak')}
                      className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-cyan-600/20 flex items-center space-x-2"
                    >
                      <Package className="w-4 h-4" />
                      <span>Launch PAK Tool</span>
                    </button>
                    <button 
                      onClick={() => setActiveTab('ai')}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition border border-slate-700 flex items-center space-x-2"
                    >
                      <Bot className="w-4 h-4" />
                      <span>Ask AI Companion</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Status Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase">PAK Workspace</span>
                    <FolderOpen className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="text-xl font-bold text-slate-100">/sdcard/FeaturesticLeaks</div>
                  <div className="text-xs text-emerald-400 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Active & Ready</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase">Target Preset</span>
                    <Layers className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="text-xl font-bold text-slate-100">Preset P1 (PUBG/BGMI)</div>
                  <div className="text-xs text-slate-400">Gameplay Core Lua Path</div>
                </div>

                <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase">Lua Compiler</span>
                    <Code2 className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="text-xl font-bold text-slate-100">LuaJIT / Lua 5.1</div>
                  <div className="text-xs text-emerald-400 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Syntax Auto-Repair Enabled</span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Quick Actions
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={() => triggerAction('1-Click Auto Lua Workflow')}
                    className="p-4 bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-xl flex items-center space-x-4 text-left transition group"
                  >
                    <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-lg group-hover:bg-cyan-500/20 transition">
                      <Zap className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">1-Click Auto Lua Workflow</div>
                      <div className="text-xs text-slate-400 mt-0.5">Auto syntax repair, bytecode compilation, and path injection.</div>
                    </div>
                  </button>

                  <button
                    onClick={() => triggerAction('Auto Offset Check')}
                    className="p-4 bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-xl flex items-center space-x-4 text-left transition group"
                  >
                    <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg group-hover:bg-blue-500/20 transition">
                      <RefreshCw className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">Auto Offset Updater</div>
                      <div className="text-xs text-slate-400 mt-0.5">Check and pull latest offset pattern definitions.</div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'pak' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white">PAK / OBB Tool</h2>
                <p className="text-xs text-slate-400 mt-1">Unpack and repack Tencent PAK archives with full integrity validation.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
                  <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
                    <Package className="w-5 h-5" />
                    <span>Unpack PAK / OBB</span>
                  </div>
                  <p className="text-xs text-slate-400">Extracts contents into <code className="text-cyan-300">/sdcard/FeaturesticLeaks/UNPACK</code></p>
                  
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-300">Select Input File</label>
                    <input 
                      type="text" 
                      placeholder="e.g. game_patch_2.5.0.pak" 
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <button 
                    onClick={() => triggerAction('Unpack PAK Archive')}
                    className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-cyan-600/20"
                  >
                    Start Unpack
                  </button>
                </div>

                <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
                  <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
                    <Package className="w-5 h-5" />
                    <span>Repack PAK / OBB</span>
                  </div>
                  <p className="text-xs text-slate-400">Repacks modified folder into <code className="text-cyan-300">/sdcard/FeaturesticLeaks/RESULT</code></p>
                  
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-slate-300">Select Repack Folder</label>
                    <input 
                      type="text" 
                      placeholder="e.g. game_patch_2.5.0" 
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <button 
                    onClick={() => triggerAction('Repack PAK Archive')}
                    className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-cyan-600/20"
                  >
                    Start Repack
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'lua' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white">Lua Compiler & Syntax Repair</h2>
                <p className="text-xs text-slate-400 mt-1">Compile Lua 5.1 scripts or auto-fix syntax errors before injection.</p>
              </div>

              <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-200">Target Path Preset</span>
                  <select 
                    value={selectedPreset}
                    onChange={(e) => setSelectedPreset(e.target.value)}
                    className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-cyan-400 font-mono focus:outline-none focus:border-cyan-500"
                  >
                    <option value="P1">Preset P1: Content/Lua/GameLua/Mod/BRMod/Gameplay/Core</option>
                    <option value="P2">Preset P2: Content/Lua/GameLua/Mod/BRMod/Gameplay</option>
                    <option value="P3">Preset P3: Content/Lua/GameLua/Mod/UI</option>
                  </select>
                </div>

                <div className="flex items-center space-x-3 pt-2">
                  <button 
                    onClick={() => triggerAction('Compile Lua Script')}
                    className="flex-1 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-cyan-600/20"
                  >
                    Compile to Bytecode
                  </button>
                  <button 
                    onClick={() => triggerAction('Lua Syntax Auto-Repair')}
                    className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition"
                  >
                    Repair Syntax Errors
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="h-full flex flex-col space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white">AI Companion & Assistant</h2>
                <p className="text-xs text-slate-400 mt-1">Ask modding questions, troubleshoot Lua errors, or guide PAK extraction.</p>
              </div>

              <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-4 min-h-[350px]">
                <div className="space-y-3 overflow-y-auto max-h-[350px] pr-2">
                  {chatMessages.map((msg, idx) => (
                    <div 
                      key={idx}
                      className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div 
                        className={`max-w-md p-3 rounded-xl text-sm leading-relaxed ${
                          msg.sender === 'user'
                            ? 'bg-cyan-600 text-white rounded-br-none'
                            : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleSendChat} className="flex items-center space-x-2">
                  <input 
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask AI anything or type a command..."
                    className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <button 
                    type="submit"
                    className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition"
                  >
                    Send
                  </button>
                </form>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white">System Console & Execution Logs</h2>
                <p className="text-xs text-slate-400 mt-1">Real-time status updates from the Python backend engine.</p>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-300 space-y-1 h-[400px] overflow-y-auto">
                {logOutput.map((log, idx) => (
                  <div key={idx} className="leading-relaxed">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
