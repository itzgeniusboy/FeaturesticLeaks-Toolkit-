import React, { useState } from 'react';
import { BookOpen, Copy, Check, Terminal, ExternalLink, ShieldAlert, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';
import { ThemeMode } from '../types';

interface SetupGuideProps {
  theme?: ThemeMode;
}

export const SetupGuide: React.FC<SetupGuideProps> = ({ theme = 'matrix' }) => {
  const themeStyles = {
    matrix: {
      accent: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      border: 'border-emerald-500/40',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500 text-slate-950',
      badge: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
      numBg: 'bg-emerald-500 text-slate-950 font-black',
    },
    cyan: {
      accent: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      border: 'border-cyan-500/40',
      buttonBg: 'bg-cyan-600 hover:bg-cyan-500 text-slate-950',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
      numBg: 'bg-cyan-500 text-slate-950 font-black',
    },
    synthwave: {
      accent: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      border: 'border-fuchsia-500/40',
      buttonBg: 'bg-fuchsia-600 hover:bg-fuchsia-500 text-slate-950',
      badge: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-500/40',
      numBg: 'bg-fuchsia-500 text-slate-950 font-black',
    },
    solar: {
      accent: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      border: 'border-amber-500/40',
      buttonBg: 'bg-amber-600 hover:bg-amber-500 text-slate-950',
      badge: 'bg-amber-950 text-amber-300 border-amber-500/40',
      numBg: 'bg-amber-500 text-slate-950 font-black',
    },
  };

  const style = themeStyles[theme] || themeStyles.matrix;
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const [copiedAll, setCopiedAll] = useState(false);

  const oneLinerCommand = `pkg update -y && pkg install -y git python php && pip install rich requests pycryptodome zstandard && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && python FeaturesticLeaks.py`;

  const steps = [
    {
      title: 'Step 1: Install Termux on Android Device',
      cmd: 'pkg update && pkg upgrade -y && pkg install git python php -y',
      desc: 'Download Termux from F-Droid or GitHub releases. Execute package updates and install Python 3, Git, and PHP.',
    },
    {
      title: 'Step 2: Clone FeaturesticLeaks Toolkit Repository',
      cmd: 'git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit-',
      desc: 'Clone the repository and enter the directory.',
    },
    {
      title: 'Step 3: Install Required Python Libraries',
      cmd: 'pip install rich requests pycryptodome zstandard',
      desc: 'Install required Python modules for Rich CLI UI, HTTP calls, cryptographic routines, and Zstandard compression.',
    },
    {
      title: 'Step 4: Launch FeaturesticLeaks.py Tool',
      cmd: 'python FeaturesticLeaks.py',
      desc: 'Launch the interactive console tool in Termux.',
    },
  ];

  const handleCopy = (cmd: string, index: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyOneLiner = () => {
    navigator.clipboard.writeText(oneLinerCommand);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-5 shadow-2xl backdrop-blur-md`}>
        <div className="flex items-center space-x-3">
          <div className={`p-3 bg-slate-950 rounded-xl border ${style.border} ${style.accent}`}>
            <BookOpen className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className={`text-lg font-black ${style.accent} ${style.accentGlow}`}>Termux Setup & Direct Android Execution Guide</h2>
            <p className="text-xs text-slate-400">Run FeaturesticLeaks.py directly inside Android Termux CLI.</p>
          </div>
        </div>
      </div>

      {/* 1-Click All-in-One Termux Auto Install Card */}
      <div className={`bg-slate-950 border-2 ${style.border} rounded-2xl p-5 shadow-2xl space-y-3 relative overflow-hidden`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className={`w-5 h-5 ${style.accent} animate-bounce`} />
            <h3 className={`text-sm font-black ${style.accent} tracking-wider uppercase`}>
              ⚡ 1-Click Auto Termux Setup Command
            </h3>
          </div>
          <span className={`text-[10px] px-2.5 py-1 rounded-full font-bold border ${style.badge}`}>
            Android Termux Ready
          </span>
        </div>

        <p className="text-xs text-slate-300">
          Copy this single command and paste it directly into your Termux app on Android. It will update packages, install Python & PHP, clone the repository, and auto-run <code className={style.accent}>FeaturesticLeaks.py</code>.
        </p>

        <div className="p-3.5 bg-black/95 rounded-xl border border-slate-800 flex items-center justify-between gap-3">
          <code className={`text-xs ${style.accent} font-extrabold overflow-x-auto whitespace-nowrap select-all pr-2`}>
            {oneLinerCommand}
          </code>
          <button
            onClick={handleCopyOneLiner}
            className={`shrink-0 px-4 py-2 rounded-xl ${style.buttonBg} text-xs font-black shadow-lg flex items-center gap-1.5 transition`}
          >
            {copiedAll ? <Check className="w-4 h-4 text-emerald-950" /> : <Copy className="w-4 h-4" />}
            <span>{copiedAll ? 'COPIED TO CLIPBOARD!' : 'COPY TERMUX COMMAND'}</span>
          </button>
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-4">
        {steps.map((step, idx) => (
          <div key={idx} className={`bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl space-y-3`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs ${style.numBg}`}>
                  {idx + 1}
                </span>
                <h3 className={`text-sm font-black ${style.accent}`}>{step.title}</h3>
              </div>
              <button
                onClick={() => handleCopy(step.cmd, idx)}
                className={`text-xs ${style.accent} hover:underline flex items-center gap-1 font-bold`}
              >
                {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedIndex === idx ? 'Copied' : 'Copy Command'}</span>
              </button>
            </div>

            <p className="text-xs text-slate-300">{step.desc}</p>

            <div className="p-3 bg-black/90 rounded-xl border border-slate-800 flex items-center justify-between text-xs overflow-x-auto">
              <code className={`${style.accent} font-bold whitespace-nowrap`}>{step.cmd}</code>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
