import React, { useState, useEffect } from 'react';
import { Key, Plus, RefreshCw, Send, ShieldAlert, CheckCircle, Clock, Trash2, Copy, Check, Terminal } from 'lucide-react';
import { VerificationResponse } from '../types';

interface KeyItem {
  key: string;
  expiry_date: string;
  registered_hwid: string | null;
  status: 'ACTIVE' | 'REVOKED';
  note: string;
  daysRemaining?: number;
  isExpired?: boolean;
}

export const KeyManager: React.FC = () => {
  const [keysList, setKeysList] = useState<KeyItem[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(false);

  // Key Creator Form State
  const [newKey, setNewKey] = useState(`PAK-KEY-${Math.floor(1000 + Math.random() * 9000)}-VIP`);
  const [daysValid, setDaysValid] = useState('30');
  const [noteInput, setNoteInput] = useState('New Client License');

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
      <div className="bg-slate-900 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-950 rounded-lg border border-emerald-500/30 text-emerald-400">
            <Key className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-emerald-400">verify.php API & License Key Manager</h2>
            <p className="text-xs text-slate-400">
              Manage active keys, test HTTP POST requests, and configure single-device HWID locks.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: License Key Generator & Database */}
        <div className="lg:col-span-7 space-y-6">
          {/* Key Creation Panel */}
          <div className="bg-slate-950 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-lg">
            <h3 className="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2">
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
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-emerald-300 focus:outline-none focus:border-emerald-500 font-bold"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Validity (Days):</label>
                <select
                  value={daysValid}
                  onChange={(e) => setDaysValid(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-emerald-300 focus:outline-none focus:border-emerald-500"
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
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-slate-300 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="sm:col-span-3 pt-2">
                <button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold py-2 rounded shadow transition flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Create & Store Key in verify.php Database</span>
                </button>
              </div>
            </form>
          </div>

          {/* Database Keys Table */}
          <div className="bg-slate-950 border border-emerald-900/80 rounded-xl p-4 shadow-lg space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                <span>Active Database Keys ({keysList.length})</span>
              </h3>
              <button
                onClick={fetchKeys}
                className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingKeys ? 'animate-spin' : ''}`} />
                <span>Refresh DB</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 px-2">Key</th>
                    <th className="py-2 px-2">Expiry</th>
                    <th className="py-2 px-2">Registered HWID</th>
                    <th className="py-2 px-2">Status</th>
                    <th className="py-2 px-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900">
                  {keysList.map((item) => (
                    <tr key={item.key} className="hover:bg-slate-900/60">
                      <td className="py-2 px-2 font-bold text-emerald-300">
                        {item.key}
                        <div className="text-[10px] text-slate-500">{item.note}</div>
                      </td>
                      <td className="py-2 px-2">
                        <span className={item.isExpired ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                          {item.expiry_date}
                        </span>
                        <div className="text-[10px] text-slate-500">{item.daysRemaining}d remaining</div>
                      </td>
                      <td className="py-2 px-2">
                        {item.registered_hwid ? (
                          <span className="text-cyan-300 font-mono text-[11px]">{item.registered_hwid}</span>
                        ) : (
                          <span className="text-amber-400 font-semibold text-[10px] bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800">
                            Unbound (Locks on use)
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-2">
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            item.status === 'ACTIVE'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : 'bg-rose-950 text-rose-300 border border-rose-800'
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-right space-x-1">
                        {item.registered_hwid && (
                          <button
                            onClick={() => handleResetHWID(item.key)}
                            title="Reset Device HWID Lock"
                            className="px-2 py-1 text-[10px] bg-amber-950 text-amber-300 border border-amber-800 rounded hover:bg-amber-900"
                          >
                            Reset HWID
                          </button>
                        )}
                        <button
                          onClick={() => handleToggleStatus(item.key)}
                          className="px-2 py-1 text-[10px] bg-slate-800 text-slate-300 border border-slate-700 rounded hover:bg-slate-700"
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

        {/* Right Column: Live API Sandbox & Endpoint Inspector */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-950 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
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
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-emerald-300 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Client Hardware ID (hwid):</label>
                <input
                  type="text"
                  value={testHwid}
                  onChange={(e) => setTestHwid(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-cyan-300 focus:outline-none"
                />
              </div>

              <button
                onClick={handleTestApi}
                disabled={isTestingApi}
                className="w-full bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold py-2 rounded shadow flex items-center justify-center gap-2 transition"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send POST Request to /api/verify</span>
              </button>
            </div>

            {/* Response Preview Box */}
            {apiResponse && (
              <div className="border border-emerald-800 rounded bg-slate-900 p-3 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-1">
                  <span className="font-bold text-emerald-400">Response JSON Body:</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      apiResponse.status === 'SUCCESS'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-500'
                        : 'bg-rose-950 text-rose-300 border border-rose-500'
                    }`}
                  >
                    {apiResponse.status}
                  </span>
                </div>
                <pre className="text-[11px] text-emerald-300 overflow-x-auto whitespace-pre bg-black p-2 rounded border border-slate-800">
                  {JSON.stringify(apiResponse, null, 2)}
                </pre>
              </div>
            )}

            {/* cURL Command Generator */}
            <div className="pt-3 border-t border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-bold flex items-center gap-1">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>cURL Terminal Command:</span>
                </span>
                <button
                  onClick={copyCurl}
                  className="text-xs text-emerald-400 hover:underline flex items-center gap-1"
                >
                  {copiedCurl ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedCurl ? 'Copied' : 'Copy cURL'}</span>
                </button>
              </div>
              <pre className="p-2.5 rounded bg-black border border-slate-800 text-[10px] text-emerald-400 overflow-x-auto">
                {curlCommand}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
