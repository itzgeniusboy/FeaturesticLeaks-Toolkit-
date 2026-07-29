import React, { useState } from 'react';
import { BookOpen, Copy, Check, Terminal, ShieldAlert, Cpu, Download, ArrowRight } from 'lucide-react';

export const SetupGuide: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const cleanCmd = 'cd ~ && rm -rf FeaturesticLeaks-Toolkit-';

  const steps = [
    {
      title: 'Step 1: Delete Old Broken Download (Clean Wipe)',
      cmd: 'cd ~ && rm -rf FeaturesticLeaks-Toolkit-',
      desc: 'Removes any old or corrupted downloaded folder from Termux home directory.',
    },
    {
      title: 'Step 2: Install Packages (Python, PHP, Git, Compilers)',
      cmd: 'pkg update -y && pkg install -y git python php clang libffi zlib make nano',
      desc: 'Installs Git, Python 3 runtime, Nano editor, PHP interpreter, and build drivers.',
    },
    {
      title: 'Step 3: Clone Repository OR Create Clean Project Folder',
      cmd: 'git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit-',
      desc: 'Clones the GitHub repository and switches into the project folder.',
    },
    {
      title: 'Step 4: Install Dependencies & Run Tool',
      cmd: 'pip install rich requests pycryptodome zstandard && python FeaturesticLeaks.py',
      desc: 'Installs required Python packages (rich, pycryptodome, zstandard) and launches FeaturesticLeaks.py.',
    },
  ];

  const handleCopy = (cmd: string, index: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const fullCleanAndInstall = 'cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python php clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard && python FeaturesticLeaks.py';

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-emerald-900/80 rounded-xl p-4 sm:p-5 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-950 rounded-lg border border-emerald-500/30 text-emerald-400">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-emerald-400">Termux Setup & Cleanup Commands</h2>
            <p className="text-xs text-slate-400">
              Clean old broken downloads and install FeaturesticLeaks PAK Tool v2.0-ULTIMATE on Termux.
            </p>
          </div>
        </div>
      </div>

      {/* Fix Missing File Box */}
      <div className="bg-emerald-950/40 border-2 border-emerald-500/60 rounded-xl p-4 sm:p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>⚡ Direct Fix for GitHub Cloned Folder:</span>
          </span>
        </div>

        <p className="text-xs text-emerald-200/90 leading-relaxed">
          Aapke GitHub repo me <code className="text-amber-300 font-bold">FeaturesticLeaks.py</code> file <code className="text-amber-300 font-bold">public/</code> folder ke andar hai. Aap niche me se koi bhi **1 command** Termux me copy-paste kar ke run karein:
        </p>

        {/* Command 1: Run directly from public */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-300">Option 1: Direct Run From Public Folder</span>
          <div className="flex items-center justify-between bg-black p-3 rounded border border-emerald-800">
            <code className="text-xs text-emerald-400 font-mono overflow-x-auto whitespace-pre">
              python public/FeaturesticLeaks.py
            </code>
            <button
              onClick={() => handleCopy('python public/FeaturesticLeaks.py', 77)}
              className="ml-2 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shrink-0"
            >
              {copiedIndex === 77 ? 'Copied!' : 'Copy Command'}
            </button>
          </div>
        </div>

        {/* Command 2: Copy to Root and Run */}
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-300">Option 2: Copy to Root Folder & Run</span>
          <div className="flex items-center justify-between bg-black p-3 rounded border border-emerald-800">
            <code className="text-xs text-emerald-400 font-mono overflow-x-auto whitespace-pre">
              cp public/FeaturesticLeaks.py . && python FeaturesticLeaks.py
            </code>
            <button
              onClick={() => handleCopy('cp public/FeaturesticLeaks.py . && python FeaturesticLeaks.py', 78)}
              className="ml-2 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shrink-0"
            >
              {copiedIndex === 78 ? 'Copied!' : 'Copy Command'}
            </button>
          </div>
        </div>
      </div>
      <div className="bg-amber-950/40 border-2 border-amber-500/60 rounded-xl p-4 sm:p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-amber-400 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>🧹 Delete Old Downloaded Tool (Clean Reset)</span>
          </span>
          <button
            onClick={() => handleCopy(cleanCmd, 88)}
            className="flex items-center space-x-1.5 px-3 py-1 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow transition"
          >
            {copiedIndex === 88 ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedIndex === 88 ? 'Copied Wipe Command!' : 'Copy Wipe Command'}</span>
          </button>
        </div>

        <p className="text-xs text-amber-200/80">
          Agar Termux me pehle ka koi adhoora ya purana folder downloaded hai jisse error aa raha hai, to is command se usko delete karein:
        </p>

        <pre className="p-3 bg-black rounded border border-amber-800 text-amber-300 text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed">
          {cleanCmd}
        </pre>
      </div>

      {/* One-Liner Express Installer Box */}
      <div className="bg-slate-950 border-2 border-emerald-500/50 rounded-xl p-4 sm:p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-emerald-400 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>⚡ Express One-Line Clean & Reinstall Command</span>
          </span>
          <button
            onClick={() => handleCopy(fullCleanAndInstall, 99)}
            className="flex items-center space-x-1.5 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs shadow transition"
          >
            {copiedIndex === 99 ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedIndex === 99 ? 'Copied Express Command!' : 'Copy Express Command'}</span>
          </button>
        </div>

        <pre className="p-3 bg-black rounded border border-emerald-800 text-emerald-300 text-xs overflow-x-auto whitespace-pre-wrap leading-relaxed">
          {fullCleanAndInstall}
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

      {/* Manual File Creation If GitHub is Empty */}
      <div className="bg-slate-950 border border-cyan-900/80 rounded-xl p-4 sm:p-5 space-y-3">
        <h3 className="text-sm font-bold text-cyan-400 flex items-center gap-2">
          <Download className="w-4 h-4 text-cyan-400" />
          <span>If FeaturesticLeaks.py is Missing in Your GitHub Repository</span>
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          Agar aapke GitHub repo me <code className="text-emerald-400">FeaturesticLeaks.py</code> missing hai, to Termux me direct file banane ke liye yeh karein:
        </p>
        <div className="p-3 bg-black rounded border border-slate-800 text-xs text-emerald-400 font-mono overflow-x-auto whitespace-pre">
          {`# Step 1: Create folder and enter
mkdir -p FeaturesticLeaks-Toolkit- && cd FeaturesticLeaks-Toolkit-

# Step 2: Open Nano Editor
nano FeaturesticLeaks.py

# Step 3: Source Code Tab se FeaturesticLeaks.py ka poora code Copy karke Paste karein
# Step 4: Ctrl + O (Save) -> Enter -> Ctrl + X (Exit)

# Step 5: Run the tool
python FeaturesticLeaks.py`}
        </div>
      </div>
    </div>
  );
};
