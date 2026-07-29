import React, { useState } from 'react';
import { FolderTree, FileCode, Folder, FileArchive, CheckCircle2, FileText, HardDrive, Cpu, Plus, Sparkles } from 'lucide-react';
import { VirtualFile, ThemeMode } from '../types';

interface FileWorkspaceProps {
  theme?: ThemeMode;
}

export const FileWorkspace: React.FC<FileWorkspaceProps> = ({ theme = 'matrix' }) => {
  const themeStyles = {
    matrix: {
      accent: 'text-emerald-400',
      accentGlow: 'text-glow-emerald',
      border: 'border-emerald-500/40',
      activeItem: 'bg-emerald-950 text-emerald-300 font-bold border border-emerald-500/50 box-glow-emerald',
      badge: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
    },
    cyan: {
      accent: 'text-cyan-400',
      accentGlow: 'text-glow-cyan',
      border: 'border-cyan-500/40',
      activeItem: 'bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/50 box-glow-cyan',
      badge: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
    },
    synthwave: {
      accent: 'text-fuchsia-400',
      accentGlow: 'text-glow-purple',
      border: 'border-fuchsia-500/40',
      activeItem: 'bg-fuchsia-950 text-fuchsia-300 font-bold border border-fuchsia-500/50 box-glow-purple',
      badge: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-500/40',
    },
    solar: {
      accent: 'text-amber-400',
      accentGlow: 'text-glow-amber',
      border: 'border-amber-500/40',
      activeItem: 'bg-amber-950 text-amber-300 font-bold border border-amber-500/50 box-glow-amber',
      badge: 'bg-amber-950 text-amber-300 border-amber-500/40',
    },
  };

  const style = themeStyles[theme] || themeStyles.matrix;

  const [selectedPath, setSelectedPath] = useState<string>('pak/results/unpack/extracted_assets.json');
  const [activeFileContent, setActiveFileContent] = useState<string>(`{
  "source_pak": "game_patch_v2.pak",
  "extracted_at": "2026-07-29T07:30:00Z",
  "magic_header": "0x5E6F7A8B",
  "encryption": "AES-256-GCM",
  "compression": "Zstandard (zstd v1.5)",
  "extracted_files": [
    "scripts/player_controller.lua",
    "textures/skin_mod_gold.tga",
    "configs/weapon_stats.json"
  ]
}`);

  const fileTree: VirtualFile[] = [
    {
      id: '1',
      name: 'pak',
      path: 'pak',
      type: 'directory',
      children: [
        { id: '1-1', name: 'original', path: 'pak/original', type: 'directory', children: [
          { id: '1-1-1', name: 'target_game.pak', path: 'pak/original/target_game.pak', type: 'file', size: 1048576, content: 'Binary Content [Magic: 0x5E6F7A8B ...]' }
        ] },
        { id: '1-2', name: 'results/unpack', path: 'pak/results/unpack', type: 'directory', children: [
          { id: '1-2-1', name: 'extracted_assets.json', path: 'pak/results/unpack/extracted_assets.json', type: 'file', size: 512 }
        ] },
        { id: '1-3', name: 'results/repack', path: 'pak/results/repack', type: 'directory', children: [
          { id: '1-3-1', name: 'modded_game_assets.pak', path: 'pak/results/repack/modded_game_assets.pak', type: 'file', size: 2097152 }
        ] }
      ]
    },
    {
      id: '2',
      name: 'lua',
      path: 'lua',
      type: 'directory',
      children: [
        { id: '2-1', name: 'original', path: 'lua/original', type: 'directory', children: [
          { id: '2-1-1', name: 'anti_cheat_check.lua', path: 'lua/original/anti_cheat_check.lua', type: 'file', size: 256, content: 'function checkSecurity()\n  return true\nend' }
        ] },
        { id: '2-2', name: 'compiled', path: 'lua/compiled', type: 'directory', children: [
          { id: '2-2-1', name: 'script.luac', path: 'lua/compiled/script.luac', type: 'file', size: 1024, content: 'LuaBytecode v5.3 [0x1B 0x4C 0x75 0x61]' }
        ] }
      ]
    },
    {
      id: '3',
      name: 'zip',
      path: 'zip',
      type: 'directory',
      children: [
        { id: '3-1', name: 'output', path: 'zip/output', type: 'directory', children: [
          { id: '3-1-1', name: 'asset_pack.zip', path: 'zip/output/asset_pack.zip', type: 'file', size: 4096 }
        ] }
      ]
    },
    {
      id: '4',
      name: 'injector',
      path: 'injector',
      type: 'directory',
      children: [
        { id: '4-1', name: 'backup', path: 'injector/backup', type: 'directory', children: [
          { id: '4-1-1', name: 'target_pak.bak', path: 'injector/backup/target_pak.bak', type: 'file', size: 1048576 }
        ] }
      ]
    }
  ];

  const handleSelectFile = (file: VirtualFile) => {
    setSelectedPath(file.path);
    if (file.content) {
      setActiveFileContent(file.content);
    } else if (file.name.endsWith('.json')) {
      setActiveFileContent(`{\n  "file_name": "${file.name}",\n  "status": "VALID",\n  "updated_at": "${new Date().toISOString()}"\n}`);
    } else {
      setActiveFileContent(`// Inspection of ${file.path}\n// File Size: ${file.size || 1024} Bytes\n// Target Architecture: Termux Android ARM64`);
    }
  };

  const renderTree = (items: VirtualFile[]) => {
    return items.map((item) => {
      const isDir = item.type === 'directory';
      const isSelected = selectedPath === item.path;
      return (
        <div key={item.id} className="ml-3 my-1 font-mono text-xs">
          <div
            onClick={() => !isDir && handleSelectFile(item)}
            className={`flex items-center space-x-2 px-2.5 py-1.5 rounded-lg cursor-pointer transition ${
              isSelected
                ? style.activeItem
                : 'text-slate-300 hover:bg-slate-900 hover:text-emerald-400'
            }`}
          >
            {isDir ? (
              <Folder className="w-4 h-4 text-cyan-400 shrink-0" />
            ) : item.name.endsWith('.pak') ? (
              <FileArchive className="w-4 h-4 text-amber-400 shrink-0" />
            ) : (
              <FileCode className={`w-4 h-4 ${style.accent} shrink-0`} />
            )}
            <span>{item.name}</span>
          </div>

          {isDir && item.children && (
            <div className="border-l border-slate-800 ml-2.5 pl-2">
              {renderTree(item.children)}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className={`bg-slate-900/90 border ${style.border} rounded-2xl p-5 shadow-2xl backdrop-blur-md`}>
        <div className="flex items-center space-x-3">
          <div className={`p-3 bg-slate-950 rounded-xl border ${style.border} ${style.accent}`}>
            <FolderTree className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className={`text-lg font-black ${style.accent} ${style.accentGlow}`}>Termux Virtual File Workspace</h2>
            <p className="text-xs text-slate-400">
              Directory structure generated by <code className={style.accent}>FeaturesticLeaks.py</code> on startup.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left Tree Inspector */}
        <div className={`md:col-span-5 bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl space-y-3`}>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs">
            <span className={`font-black ${style.accent}`}>Termux Workspace Directories</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${style.badge}`}>Auto-Created</span>
          </div>

          <div className="overflow-y-auto max-h-[480px]">
            {renderTree(fileTree)}
          </div>
        </div>

        {/* Right Content Viewer */}
        <div className={`md:col-span-7 bg-slate-950 border ${style.border} rounded-2xl p-5 shadow-xl space-y-3`}>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs">
            <span className={`font-bold ${style.accent}`}>Viewing File: <code className="text-cyan-300">{selectedPath}</code></span>
            <span className="text-xs text-slate-400">Read-Only Preview</span>
          </div>

          <div className="bg-black/95 border border-slate-800 rounded-xl p-4">
            <pre className={`text-xs ${style.accent} overflow-x-auto whitespace-pre font-mono leading-relaxed`}>
              {activeFileContent}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
