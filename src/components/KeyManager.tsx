import React, { useState, useEffect } from 'react';
import { Key, Plus, RefreshCw, Send, ShieldAlert, CheckCircle, Clock, Trash2, Copy, Check, Terminal, Sparkles } from 'lucide-react';
import { VerificationResponse, ThemeMode } from '../types';

interface KeyItem {
  key: string;
  expiry_date: string;
  registered_hwid: string | null;
  status: 'ACTIVE' | 'REVOKED';
  note: string;
  daysRemaining?: number;
  isExpired?: boolean;
}

interface KeyManagerProps {
  theme?: ThemeMode;
}

export const KeyManager: React.FC<KeyManagerProps> = ({ theme = 'matrix' }) => {
  const themeStyles = {
    matrix: {
      accent: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      border: 'border-emerald-500/40',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500 text-slate-950',
      badge: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
    },
    cyan: {
      accent: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      border: 'border-cyan-500/40',
      buttonBg: 'bg-cyan-600 hover:bg-cyan-500 text-slate-950',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
    },
    synthwave: {
      accent: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      border: 'border-fuchsia-500/40',
      buttonBg: 'bg-fuchsia-600 hover:bg-fuchsia-500 text-slate-950',
      badge: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-500/40',
    },
    solar: {
      accent: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      border: 'border-amber-500/40',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-slate-950',
      badge: 'bg-amber-950 text-amber-300 border-amber-500/40',
    },
  };

  const style = themeStyles[theme] || themeStyles.matrix;

  const [keysList, setKeysList] = useState<KeyItem[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(false);

  // Key Creator Form State
  const [newKey, setNewKey] = useState(`PAK-KEY-${Math.floor(1000 + Math.random() * 9000)}-VIP`);
  const [daysValid, setDaysValid] = useState('30');
  const [noteInput, setNoteInput] = useState('New VIP License');

  // API Tester State
  const [testKey, setTestKey] = useState('PAK-VIP-9999-ULTIMATE');
  const [testHwid, setTestHwid] = useState('FL-HWID-3A7F92B0C41E8D5A');
  const [apiResponse, setApiResponse] = useState<VerificationResponse | null>(null);
  const [isTestingApi, setIsTestingApi] = useState(false);
  const [copiedCurl, setCopiedCurl] = useState(false);

  const fetchKeys = async () => {
    setIsLoadingKeys(true);
    try {
      const res = await fetch('/api/admin/keys');
      if (res.ok) {
        const data = await res.json();
        setKeysList(data);
      }
    } catch (e) {
      console.error('Failed to fetch keys', e);
    } finally {
      setIsLoadingKeys(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/admin/keys/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: newKey, daysValid: parseInt(daysValid), note: noteInput }),
      });
      if (res.ok) {
        setNewKey(`PAK-KEY-${Math.floor(1000 + Math.random() * 9000)}-VIP`);
        fetchKeys();
      }
    } catch (e) {
      console.error('Error creating key', e);
    }
  };

  const handleResetHWID = async (key: string) => {
    try {
      const res = await fetch('/api/admin/keys/reset-hwid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
      if (res.ok) {
        fetchKeys();
      }
    } catch (e) {
      console.error('HWID reset error', e);
    }
  };

  const handleToggleStatus = async (key: string) => {
    try {
      const res = await fetch('/api/admin/keys/toggle-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
      if (res.ok) {
        fetchKeys();
      }
    } catch (e) {
      console.error('Status toggle error', e);
    }
  };

  const handleTestApi = async () => {
    setIsTestingApi(true);
    try {
      const res = await fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ key: testKey, hwid: testHwid }),
      });
      const data = await res.json();
      setApiResponse(data);
    } catch (e: any) {
      setApiResponse({
        status: 'INVALID',
        message: e.message || 'Connection failed',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsTestingApi(false);
    }
  };

  const curlCommand = `curl -X POST "${window.location.origin}/api/verify" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "key=${testKey}&hwid=${testHwid}"`;

  const copyCurl = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopiedCurl(true);
    setTimeout(() => setCopiedCurl(false), 2000);
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-5 shadow-2xl backdrop-blur-md`}>
        <div className="flex items-center space-x-3">
          <div className={`p-3 bg-slate-950 rounded-xl border ${style.border} ${style.accent}`}>
            <Key className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className={`text-lg font-black ${style.accent} ${style.accentGlow}`}>
              verify.php API & License Key Manager
            </h2>
            <p className="text-xs text-slate-400">
              Manage database keys, test HTTP POST verification, and configure device locks.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Key Creation Form */}
          <div className={`bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl`}>
            <h3 className={`text-sm font-black ${style.accent} mb-4 flex items-center gap-2`}>
              <Plus className="w-4 h-4" />
              <span>Generate New License Key</span>
            </h3>

            <form onSubmit={handleCreateKey} className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">License Key String:</label>
                <input
                  type="text"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-2 ${style.accent} font-bold focus:outline-none`}
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Validity (Days):</label>
                <select
                  value={daysValid}
                  onChange={(e) => setDaysValid(e.target.value)}
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-2 ${style.accent} focus:outline-none`}
                >
                  <option value="7">7 Days</option>
                  <option value="30">30 Days</option>
                  <option value="90">90 Days</option>
                  <option value="365">1 Year (365 Days)</option>
                  <option value="3650">VIP Lifetime</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Client / Note:</label>
                <input
                  type="text"
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  placeholder="Note / User ID"
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-2 text-slate-200 focus:outline-none`}
                />
              </div>

              <div className="sm:col-span-3 pt-2">
                <button
                  type="submit"
                  className={`w-full ${style.buttonBg} font-extrabold py-2.5 rounded-xl shadow-lg transition flex items-center justify-center gap-2`}
                >
                  <Plus className="w-4 h-4" />
                  <span>Create & Store Key in verify.php Database</span>
                </button>
              </div>
            </form>
          </div>

          {/* Database Keys Table */}
          <div className={`bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl space-y-4`}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className={`text-sm font-black ${style.accent} flex items-center gap-2`}>
                <span>Active Database Keys ({keysList.length})</span>
              </h3>
              <button
                onClick={fetchKeys}
                className={`text-xs text-slate-400 hover:${style.accent} flex items-center gap-1.5 transition`}
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingKeys ? 'animate-spin' : ''}`} />
                <span>Refresh DB</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2.5 px-2">Key</th>
                    <th className="py-2.5 px-2">Expiry</th>
                    <th className="py-2.5 px-2">Registered HWID</th>
                    <th className="py-2.5 px-2">Status</th>
                    <th className="py-2.5 px-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900">
                  {keysList.map((item) => (
                    <tr key={item.key} className="hover:bg-slate-900/60 transition-colors">
                      <td className={`py-3 px-2 font-black ${style.accent}`}>
                        {item.key}
                        <div className="text-[10px] text-slate-500 font-normal">{item.note}</div>
                      </td>
                      <td className="py-3 px-2">
                        <span className={item.isExpired ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                          {item.expiry_date}
                        </span>
                        <div className="text-[10px] text-slate-500">{item.daysRemaining}d remaining</div>
                      </td>
                      <td className="py-3 px-2">
                        {item.registered_hwid ? (
                          <span className="text-cyan-300 font-mono text-[11px]">{item.registered_hwid}</span>
                        ) : (
                          <span className="text-amber-400 font-bold text-[10px] bg-amber-950/80 px-2 py-0.5 rounded-full border border-amber-800">
                            Unbound (Locks on use)
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-2">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                            item.status === 'ACTIVE'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                              : 'bg-rose-950 text-rose-300 border border-rose-500/40'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-right space-x-1.5">
                        {item.registered_hwid && (
                          <button
                            onClick={() => handleResetHWID(item.key)}
                            className="px-2.5 py-1 text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800 rounded-lg hover:bg-amber-900"
                          >
                            Reset HWID
                          </button>
                        )}
                        <button
                          onClick={() => handleToggleStatus(item.key)}
                          className="px-2.5 py-1 text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700 rounded-lg hover:bg-slate-700"
                        >
                          Toggle
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-5 space-y-6">
          <div className={`bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl space-y-4`}>
            <h3 className={`text-sm font-black ${style.accent} flex items-center gap-2`}>
              <Send className="w-4 h-4" />
              <span>PHP API Live Endpoint Sandbox</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Target Key:</label>
                <input
                  type="text"
                  value={testKey}
                  onChange={(e) => setTestKey(e.target.value)}
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-2 ${style.accent} focus:outline-none`}
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Hardware ID (HWID):</label>
                <input
                  type="text"
                  value={testHwid}
                  onChange={(e) => setTestHwid(e.target.value)}
                  className={`w-full bg-slate-900 border border-slate-800 focus:${style.border} rounded-lg px-3 py-2 text-cyan-300 focus:outline-none`}
                />
              </div>

              <button
                onClick={handleTestApi}
                disabled={isTestingApi}
                className="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-extrabold py-2.5 rounded-xl shadow-lg flex items-center justify-center gap-2 transition"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send POST Request to /api/verify</span>
              </button>
            </div>

            {/* Response Preview */}
            {apiResponse && (
              <div className="border border-slate-800 rounded-xl bg-slate-900 p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                  <span className={`font-bold ${style.accent}`}>Response JSON:</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                      apiResponse.status === 'SUCCESS'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-500'
                        : 'bg-rose-950 text-rose-300 border border-rose-500'
                    }`}
                  >
                    {apiResponse.status}
                  </span>
                </div>
                <pre className={`text-[11px] ${style.accent} overflow-x-auto whitespace-pre bg-black/90 p-3 rounded-lg border border-slate-800`}>
                  {JSON.stringify(apiResponse, null, 2)}
                </pre>
              </div>
            )}

            {/* cURL Command Generator */}
            <div className="pt-3 border-t border-slate-800/80 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-bold flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>cURL Command:</span>
                </span>
                <button
                  onClick={copyCurl}
                  className={`text-xs ${style.accent} hover:underline flex items-center gap-1 font-bold`}
                >
                  {copiedCurl ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedCurl ? 'Copied' : 'Copy cURL'}</span>
                </button>
              </div>
              <pre className={`p-3 rounded-xl bg-black/90 border border-slate-800 text-[10px] ${style.accent} overflow-x-auto`}>
                {curlCommand}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
