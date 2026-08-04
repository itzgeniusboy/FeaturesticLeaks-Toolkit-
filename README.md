# ⚡ FEATURESTIC LEAKS PAK & LUA MASTER SUITE v2.7

> **Termux / Android Game Reverse Engineering, High-Speed PAK Manipulation & Universal Lua Suite**  
> Complete high-performance reverse engineering suite for unpacking, repacking, path-injecting, rebuilding Unreal Engine / Tencent `.pak` & `.obb` containers, dumping skin assets, UAsset/UExp auto-pairing, AI Lua repair, and managing Lua bytecode natively on Termux, Android Linux, and PC.

---

## 👤 Developer & Official Credits

* **Developer Telegram**: [@L359D](https://t.me/L359D) (VIP Developer)
* **Official Telegram Channel**: [https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)
* **Tool Version**: `FeaturesticLeaks PAK & LUA Master Suite v2.7`
* **Supported Platform**: Termux / Android Linux / Windows / Linux

---

## 🚀 Termux Installation & Quick Start

Termux open karke is single command ko copy-paste karke Enter press karein:

### ⚡ Express One-Line Command (Fresh Setup & Launch)

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard pytz gmalg && python FeaturesticLeaks.py
```

📖 **Detailed Usage Manual**: Detailed feature guides and step-by-step instructions ke liye **[DOCUMENTATION.md](./DOCUMENTATION.md)** dekhein.

---

## 🛠️ Step-by-Step Manual Setup

Agar aap single-command ki bajaye step-by-step setup karna chahte hain:

### **Step 1: Storage Permission Dijiye**
```bash
termux-setup-storage
```

### **Step 2: Termux System Packages Install Karein**
```bash
pkg update -y && pkg install -y git python clang libffi zlib make nano
```

### **Step 3: Python Dependencies Install Karein**
```bash
pip install rich requests pycryptodome zstandard pytz gmalg
```

### **Step 4: Repository Clone Karein**
```bash
cd ~ && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git
```

### **Step 5: Project Directory Enter Karein**
```bash
cd FeaturesticLeaks-Toolkit-
```

### **Step 6: Tool Launch Karein**
```bash
python FeaturesticLeaks.py
```

---

## 💡 Quick Launch Shortcuts & One-Click Auto-Update

Shortcut commands through tool ko Termux me kisi bhi location se launch kar sakte hain:

1. **`leak` Command** (Main Category Menu):
   ```bash
   leak
   ```
2. **Category Direct Termux Shortcuts**:
   ```bash
   leak pak     # Launch PAK & OBB Tools Menu directly
   leak lua     # Launch LUA Master Suite directly
   leak watch   # Launch Watch Mode Engine directly
   leak ai      # Launch AI Tools & Multi-API Key Manager
   leak utils   # Launch Utilities & Setup Menu
   leak update  # Run Instant Auto-Updater
   ```
3. **`paktool` Command**:
   ```bash
   paktool
   ```
4. **🚀 Instant Auto-Update & Update Banner System**:
   - **Boot Update Banner**: Tool startup par GitHub check karta hai. Agar update available hai, toh banner notification screen par dikhayega.
   - **Interactive One-Click Update**: Main Menu par **`U`** press karein ya **Utilities Menu -> Option [9] Check Tool Update** select karein. Tool update download karke, syntax verify karega, `.py.bak` backup create karega, aur auto-restart kar dega.

---

## 📂 Category-Wise Modular Menu Architecture

Tool visual layout is restructured into clean, high-performance category menus:

```text
⚡ MAIN CATEGORY MENU
├── [1] 🤖 AI Assistant & Modder  --> 1-Click AI Companion for Auto Unpack, Repack, Lua Inject & Modding
├── [2] 📦 PAK Tools             --> Unpack, Repack, Replace, Inject, Skin Swapper, OBB Manager
├── [3] 🌙 LUA Tools             --> Compile, Decompile, Script Merger, Obfuscator, Universal Packer
├── [4] 🔑 OpenCode API & Settings--> Manage OpenCode API Keys (Multi-Key Auto Rotation), Base URL & Telegram Bot
└── [U] 🚀 Auto-Update           --> One-touch GitHub auto-update & auto-restart engine
```

---

## 📂 Clean & Organized Workspace Structure

Tool launch hote hi SDCard (`/sdcard/FeaturesticLeaks/`) me structured workspace system automatically setup ho jata hai, jisse File Manager (ZArchiver) bilkul clean rehta hai:

```text
/sdcard/FeaturesticLeaks/
├── 📦 PAK_WORKSPACE/            <-- Everything related to PAK & OBB Modding
│   ├── 📥 1_PAK_INPUT/          <-- Put original game .pak / .obb files here
│   ├── 📂 2_UNPACK/             <-- Extracted folders & assets
│   ├── ✏️ 3_REPLACE/            <-- Put edited files here for replacement mode
│   ├── 💉 4_INJECT/             <-- Put custom files for direct path injection
│   └── 🚀 5_RESULT/             <-- Final repacked .pak & .obb files
│
├── 🌙 LUA_WORKSPACE/            <-- Everything related to Lua Scripts Modding
│   ├── 📜 1_LUA_INPUT/          <-- Put .lua / .luac scripts here
│   ├── 🔓 2_DECOMPILED/         <-- Decompiled .lua source files
│   ├── ⚙️ 3_COMPILED/           <-- Compiled .luac bytecode files
│   └── 🎉 4_RESULT/             <-- Final processed & merged scripts
│
└── 📋 LOGS/                    <-- System logs & auto-trimmed debug reports
```

> 💡 **Clean File Manager Experience**: Bikhre hue temporary folders auto-clean ho jaate hain. Aap ZArchiver me direct `/sdcard/FeaturesticLeaks/` open karke easily manage kar sakte hain.

---

## 🧰 Complete Feature Overview

### 📦 1. PAK / OBB Tools
1. **Multi-Threaded PAK Unpacker**: Multi-threaded engine (up to 32 worker threads) supporting SM4/AES decryption, Zstandard/OBB decompression, and automatic CRC32 stem hash auto-repair for corrupt PAK headers.
2. **Repack All Types PAKs**: Auto-detects container modes (`MINI_OBB`, `GAMEPATCH`, `OBBZSDIC`) and rebuilds container blocks with high efficiency.
3. **Replace Existing Files**: Size-independent byte replacer that modifies existing PAK files without crash or header corruption issues.
4. **Inject Path (New Files)**: Direct path injector for inserting custom files/folders directly into target internal game directories (e.g., `Content/Lua/GameLua/Mod/...`). Features auto-in-place Lua 5.1 syntax repair, temporary file auto-cleanup, and strict workspace sync so deleted files never get re-injected.
5. **One-Click Mods**: White body mesh nuller & character asset converter.
6. **Skin ID Swap & Asset Dumper**:
   - Swaps Lobby, Ingame, Weapon, Hit Effect & Deadbox skin IDs inside `.uasset` / `.uexp` binaries.
   - **Skin Asset Dumper**: Scans PAK files or UNPACK folders for skin textures, meshes, uassets/uexps, generates `.txt` and `.json` reports, and exports raw skin assets.
7. **OBB Manager**: Extract and rezip OBB containers with byte-exact padding to match original file sizes.
8. **UAsset / UExp Sync Engine**: Auto-pairs companion `.uasset` and `.uexp` files when selecting files and warns if a companion asset is missing in the game directory. Includes keyword filtering `[F]`.

### 🌙 2. Lua Master Suite
1. **Compile Lua**: Converts `.lua` source code into `.luac` bytecode.
2. **Decompile Lua**: Converts `.luac` bytecode back to readable `.lua` source text.
3. **Embed PAK into Lua**: Converts `.pak` into Base64 payload and embeds it directly into a GameGuard Lua installer script.
4. **Universal Pack & Unpack Lua**: Encodes/decodes Lua scripts using extensible plugin architecture with fixed 8-byte ASCII tags (`B64_____`, `XOR_____`, `ZLIB____`, `RAW_____`).
5. **Lua String Obfuscator & Dumper Engine**: Encrypts string literals with Hex/Base64/XOR wrappers and dumps URLs/IPs.
6. **Anti-Bypass & Security Analyzer**: Audits Lua scripts for GameGuard memory calls and outputs a 0-100 risk score report.
7. **Bytecode Header Fixer**: Repairs corrupted magic headers for Lua 5.1 (`1B 4C 75 61 51 00...`) or LuaJIT (`1B 4C 4A 02...`).
8. **Lua Script Merger**: Merges multiple `.lua` scripts into a clean, modular `Master_Merged_Script.lua` file wrapped in `do...end` blocks.

### 🤖 3. OpenCode AI Modder & Multi-Key Engine
1. **1-Click AI Companion & Watcher**: Real-time interactive AI companion for automated PAK unpacking/repacking, Lua script generation, syntax auto-repair, and modding guidance.
2. **OpenCode Unlimited API Engine**: Powered by primary OpenCode custom models (`opencode-modding-v1`, `qwen2.5-coder`, or custom OpenAI-compatible endpoints) with multi-key auto-rotation.
3. **Direct Key Setup**: Direct key acquisition portal link `https://opencode.ai/auth` included inside settings menu with multi-key support (`key1, key2, key3`).
4. **Auto Error Handler & Fallback**: Robust error fallback mechanism preventing JSON parse crashes and providing silent retry handling.

### 🛠️ 4. Utilities, Diagnostic & Auto-Updater
1. **UE4 String Tool**: Extract and repack readable string literals inside `.uasset` / `.uexp` binary files.
2. **File Finder**: Search files inside PAK structure by keyword or extension.
3. **Termux Auto-Setup**: Configures `leak` global terminal command and SDCard directories automatically.
4. **File Resizer & Equalizer**: Match exact byte size of any PAK, OBB, or LUA file.
5. **Workspace Cleanup**: Easily clear temporary working folders to free up storage space.
6. **Check Tool Update 🚀 (`[U]`)**: Force instant GitHub update check to download verified updates and auto-restart.
7. **Diagnostic & Benchmark ⚡ (`Option [10]`)**: Real-time system RAM inspection, Lua compiler speed test (in ms), and automatic log hygiene.
8. **Watch Mode 👁️**: Monitors PAK and LUA input folders in real-time with direct menu shortcuts (`[1]-[5]`, `[U]`, `[help]`).
9. **Filtered Telegram Bug Reporter**: Sends silent crash reports for actual code bugs to developer Telegram bot, while filtering out normal API limits and file missing notices.

---

## 👤 Developer Contact & Official Credits

* **Main Developer**: **[@L359D](https://t.me/L359D)**
* **Official Telegram Channel**: **[t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Platform**: Termux / Android Linux / Windows / Linux

