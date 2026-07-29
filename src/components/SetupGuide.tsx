import React, { useState } from 'react';
import { BookOpen, Copy, Check, Terminal, ShieldAlert, Cpu, Download, ArrowRight } from 'lucide-react';

export const SetupGuide: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const steps = [
    {
      title: 'Step 1: Update & Install Git, Python, PHP',
      cmd: 'pkg update -y && pkg install -y git python php clang libffi zlib make',
      desc: 'Installs Git, Python 3 runtime, PHP interpreter for verify.php API testing, and build chains.',
    },
    {
      title: 'Step 2: Clone GitHub Repository & Enter Directory',
      cmd: 'git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit-',
      desc: 'Clones the single-file FeaturesticLeaks repository and switches into the workspace directory.',
    },
    {
      title: 'Step 3: Storage Permissions (Optional for File Extractor)',
      cmd: 'termux-setup-storage',
      desc: 'Grants Termux storage access to read/write game assets from Android storage (/sdcard/).',
    },
    {
      title: 'Step 4: Execute Auto-Launcher Script',
      cmd: 'chmod +x run.sh && ./run.sh',
      desc: 'Installs required Python packages (rich, pycryptodome, zstandard) and launches FeaturesticLeaks.py.',
    },
  ];

  const handleCopy = (cmd: string, index: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const fullOneLiner = 'pkg update -y && pkg install -y git python php clang libffi zlib make && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && chmod +x run.sh && ./run.sh';

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-950 rounded-lg border border-emerald-500/30 text-emerald-400">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-emerald-400">Termux Installation & Quickstart Setup Guide</h2>
            <p className="text-xs text-slate-400">
              Complete command sequence for setting up Python, PHP, Rich UI, and Cryptographic drivers on Termux Android.
            </p>
          </div>
        </div>
      </div>

      {/* One-Liner Express Installer Box */}
      <div className="bg-slate-950 border-2 border-emerald-500/50 rounded-xl p-4 sm:p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-emerald-400 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>⚡ Express One-Line Auto Installer</span>
          </span>
          <button
            onClick={() => handleCopy(fullOneLiner, 99)}
            className="flex items-center space-x-1.5 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs shadow transition"
          >
            {copiedIndex === 99 ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedIndex === 99 ? 'Copied Command!' : 'Copy Express Command'}</span>
          </button>
        </div>

        <pre className="p-3 bg-black rounded border border-emerald-800 text-emerald-300 text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed">
          {fullOneLiner}
        </pre>
      </div>

      {/* Detailed Step by Step sequence */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={index} className="bg-slate-950 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-md space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-emerald-400">{step.title}</h3>
              <button
                onClick={() => handleCopy(step.cmd, index)}
                className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-emerald-900 text-xs text-emerald-300 border border-slate-700 hover:border-emerald-500 font-bold transition"
              >
                {copiedIndex === index ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedIndex === index ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            <p className="text-xs text-slate-400">{step.desc}</p>

            <div className="p-3 bg-black rounded border border-slate-800 text-xs text-cyan-300 font-mono overflow-x-auto">
              $ {step.cmd}
            </div>
          </div>
        ))}
      </div>

      {/* Troubleshooting & Permissions */}
      <div className="bg-slate-900 border border-amber-900/60 rounded-xl p-4 sm:p-5 space-y-3">
        <h3 className="text-sm font-bold text-amber-400 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" />
          <span>Troubleshooting & Storage Permissions in Termux</span>
        </h3>
        <ul className="text-xs text-slate-300 space-y-2 list-disc list-inside">
          <li>
            <strong className="text-amber-300">Storage Access:</strong> Run <code className="text-cyan-300">termux-setup-storage</code> in Termux to grant permission to read/write game assets from Android internal storage (`/sdcard/`).
          </li>
          <li>
            <strong className="text-amber-300">Android HWID Detection:</strong> If <code className="text-cyan-300">getprop ro.serialno</code> returns empty or permission denied on Android 10+, the script automatically falls back to product model ID and machine-id SHA256 hashes.
          </li>
          <li>
            <strong className="text-amber-300">verify.php Server Hosting:</strong> Ensure your PHP backend API is hosted on a public VPS / CPanel / local server and update <code className="text-cyan-300">API_ENDPOINT</code> inside <code className="text-cyan-300">FeaturesticLeaks.py</code>.
          </li>
        </ul>
      </div>
    </div>
  );
};
