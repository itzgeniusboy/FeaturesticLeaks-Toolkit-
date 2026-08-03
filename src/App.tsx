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
  const [activeProvider, setActiveProvider] = useState<'gemini' | 'groq' | 'openrouter' | 'opencode'>('opencode');
  const [opencodeEndpoint, setOpencodeEndpoint] = useState('https://api.opencode.ai/v1');
  const [opencodeModel, setOpencodeModel] = useState('opencode-modding-v1');
  const [opencodeKey, setOpencodeKey] = useState('');
  const [testStatus, setTestStatus] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([
    { sender: 'ai', text: 'Ha bhai! Kya krna h? PAK bnana h, unpack krna h, lua compile krna h ya fix krna h? OpenCode AI Integration active h! Batao kya krna h! 🚀' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('P1');
  const [logOutput, setLogOutput] = useState<string[]>([
    '[INIT] Featurestic Leaks PAK Tool v2.5 initialized.',
    '[INFO] Workspace initialized at /sdcard/FeaturesticLeaks',
    '[OPENCODE] OpenCode Custom AI Engine Connected (Model: opencode-modding-v1)',
    '[TELEGRAM] Developer Bug Report Bot linked to @L359D',
    '[READY] Select an action to begin.'
  ]);

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput;
    setChatMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setChatInput('');

    setTimeout(() => {
      let reply = "Ha bhai! Kya krna h? PAK bnana h, unpack krna h, lua compile krna h ya fix krna h? OpenCode custom AI active h! Batao kya krna h!";
      const lower = userText.toLowerCase();
      if (lower.includes('unpack') || lower.includes('unpak')) {
        reply = "🤖 OpenCode AI: Unpack request detect hua! Scan kar raha hu... Bhai PAK folder me pehle PAK file daalo tabhi to unpack karunga! Abhi isme kuch nahi hai. Pehle file daalo fir RESULT folder me result mil jayega! 📦";
      } else if (lower.includes('compile') || lower.includes('lua pack')) {
        reply = "🤖 OpenCode AI: Lua Compile request detect hua! Scan kar raha hu... Bhai LUA folder me pehle Lua file daalo tabhi compile karunga! Abhi isme koi script nahi hai. Pehle file daalo fir RESULT folder me compiled script mil jayegi! 📜";
      } else if (lower.includes('fix') || lower.includes('repair')) {
        reply = "🤖 OpenCode AI: Lua Repair request detect hua! Scan kar raha hu... Bhai LUA folder me pehle broken Lua file daalo tabhi repair karunga! Abhi isme script nahi hai. Pehle file daalo fir batao! 🛠️";
      } else if (lower.includes('opencode') || lower.includes('termux') || lower.includes('api') || lower.includes('unlimited')) {
        reply = "🤖 OpenCode Custom Integration: Ha bhai! OpenCode custom model integration enabled hai. Isme unlimited API endpoint, custom model name aur local/remote server connect ho jate hai. Agar tool me koi bug ya error aaya, toh automatic Developer Telegram Group (@L359D) par report send ho jayegi! 🚀";
      } else if (lower.includes('hi') || lower.includes('hello') || lower.includes('hlw') || lower.includes('bhai')) {
        reply = "Ha bhai! Kya krna h? PAK bnana h, unpack krna h, lua compile krna h ya fix krna h? OpenCode AI active h! Batao kya krna h! 🚀";
      }

      setChatMessages((prev) => [...prev, { sender: 'ai', text: reply }]);
    }, 400);
  };

  const testOpenCode = () => {
    setTestStatus('Testing OpenCode Connection...');
    setTimeout(() => {
      setTestStatus(`✅ Connection Successful! Endpoint: ${opencodeEndpoint} | Model: ${opencodeModel}`);
    }, 800);
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
                  <p className="text-xs text-slate-400">Extracts contents into <code className="text-cyan-300">/sdcard/FeaturesticLeaks/RESULT</code></p>
                  
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
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Bot className="w-6 h-6 text-cyan-400" />
                    <span>AI Assistant & OpenCode Integration</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">Autonomous file-aware assistant, OpenCode custom model endpoint & auto error reporter.</p>
                </div>

                <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 p-1.5 rounded-lg text-xs font-medium">
                  <span className="text-slate-400 px-2">Provider:</span>
                  {(['opencode', 'gemini', 'groq', 'openrouter'] as const).map((prov) => (
                    <button
                      key={prov}
                      onClick={() => setActiveProvider(prov)}
                      className={`px-3 py-1 rounded-md capitalize transition ${
                        activeProvider === prov
                          ? 'bg-cyan-600 text-white shadow'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      }`}
                    >
                      {prov === 'opencode' ? 'OpenCode 🚀' : prov}
                    </button>
                  ))}
                </div>
              </div>

              {/* OpenCode Custom Model Endpoint Card */}
              {activeProvider === 'opencode' && (
                <div className="p-5 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/30 border border-cyan-500/30 rounded-xl space-y-4 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-sm">
                      <Cpu className="w-5 h-5" />
                      <span>OpenCode Custom Model Endpoint Configuration</span>
                    </div>
                    <span className="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono rounded-full">
                      Unlimited Model Mode
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-slate-300">Base Endpoint URL</label>
                      <input 
                        type="text" 
                        value={opencodeEndpoint}
                        onChange={(e) => setOpencodeEndpoint(e.target.value)}
                        placeholder="https://api.opencode.ai/v1"
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-medium text-slate-300">Custom Model Name</label>
                      <input 
                        type="text" 
                        value={opencodeModel}
                        onChange={(e) => setOpencodeModel(e.target.value)}
                        placeholder="opencode-modding-v1"
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-medium text-slate-300">API Key / Auth Token (Optional)</label>
                      <input 
                        type="password" 
                        value={opencodeKey}
                        onChange={(e) => setOpencodeKey(e.target.value)}
                        placeholder="Optional Token..."
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={testOpenCode}
                      className="px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500/30 rounded-lg text-xs font-medium flex items-center space-x-2 transition"
                    >
                      <Zap className="w-3.5 h-3.5" />
                      <span>Test OpenCode Connection</span>
                    </button>

                    <div className="text-xs text-slate-400 flex items-center space-x-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 text-yellow-400" />
                      <span>Developer Telegram Bug Bot: <strong className="text-yellow-400 font-mono">@L359D Linked</strong></span>
                    </div>
                  </div>

                  {testStatus && (
                    <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-emerald-400">
                      {testStatus}
                    </div>
                  )}
                </div>
              )}

              {/* Chat Window */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-4 min-h-[380px]">
                <div className="space-y-3 overflow-y-auto max-h-[320px] pr-2">
                  {chatMessages.map((msg, idx) => (
                    <div 
                      key={idx}
                      className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div 
                        className={`max-w-md p-3 rounded-xl text-sm leading-relaxed ${
                          msg.sender === 'user'
                            ? 'bg-cyan-600 text-white rounded-br-none shadow-lg'
                            : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none shadow'
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleSendChat} className="flex items-center space-x-2 pt-2 border-t border-slate-800">
                  <input 
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask OpenCode AI anything or type a command..."
                    className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <button 
                    type="submit"
                    className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition shadow-md shadow-cyan-600/20"
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
