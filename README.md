# ⚡ FEATURESTIC LEAKS PAK & LUA MASTER SUITE v2.8 ⚡

> **Termux / Android Game Reverse Engineering, High-Speed PAK Manipulation & Universal Lua Suite**  
> Complete high-performance reverse engineering toolkit for unpacking, repacking, path-injecting, rebuilding Unreal Engine / Tencent `.pak` & `.obb` containers, dumping skin assets, UAsset/UExp auto-pairing, AI-powered function scanning & Lua mod generation, and managing Lua bytecode natively on Termux, Android Linux, and PC.

---

## 👤 Developer & Official Credits

| Category | Details & Links |
| :--- | :--- |
| **👑 Main Developer** | [**@L359D**](https://t.me/L359D) (VIP Developer) |
| **📢 Official Telegram Channel** | [**t.me/FeaturesticLeaks**](https://t.me/FeaturesticLeaks) |
| **🐙 Official GitHub Repository** | [**itzgeniusboy/FeaturesticLeaks-Toolkit-**](https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-) |
| **⚡ Current Version** | **v2.8 Master Suite** |
| **📱 Supported Platforms** | **Termux (Android)**, **Linux (Debian/Ubuntu/Arch)**, **Windows (WSL / Native Python)** |

---

## 🚀 Termux Installation & Quick Start

Termux open karke is **Express Single Command** ko copy-paste karke Enter press karein:

### ⚡ Express 1-Line Command (Instant Setup & Launch)

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard pytz gmalg && python FeaturesticLeaks.py
```

📖 **Complete User Manual**: Har feature aur workflow ke deep step-by-step guide ke liye **[DOCUMENTATION.md](./DOCUMENTATION.md)** check karein.

---

## 🛠️ Step-by-Step Manual Setup

Agar aap step-by-step install karna chahte hain:

### **Step 1: Storage Permission Allow Karein**
```bash
termux-setup-storage
```

### **Step 2: Termux System Packages Update & Install**
```bash
pkg update -y && pkg install -y git python clang libffi zlib make nano
```

### **Step 3: Required Python Packages Install**
```bash
pip install rich requests pycryptodome zstandard pytz gmalg
```

### **Step 4: Repository Clone Karein**
```bash
cd ~ && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git
```

### **Step 5: Project Directory Me Enter Karein**
```bash
cd FeaturesticLeaks-Toolkit-
```

### **Step 6: Tool Launch Karein**
```bash
python FeaturesticLeaks.py
```

---

## 💡 Quick Launch Shortcuts & Commands

Tool setup hone ke baad aap Termux me kisi bhi folder se direct shortcuts use kar sakte hain:

### 1. Global Terminal Shortcuts
| Command | Action / Target Menu |
| :--- | :--- |
| **`leak`** | 🏠 Launch Main FeaturesticLeaks Menu |
| **`leak ai`** | 🤖 Direct Open AI Assistant & Function Modder Menu |
| **`leak pak`** | 📦 Direct Open PAK / OBB Tools Menu |
| **`leak lua`** | 🌙 Direct Open LUA Master Suite Menu |
| **`leak watch`** | 👁️ Direct Launch Real-Time Auto-Watch Engine |
| **`leak utils`** | 🛠️ Direct Open Utilities, Patcher & Guides Menu |
| **`leak update`** | 🚀 Run 1-Click Instant GitHub Auto-Updater |
| **`leak bot`** | 🤖 Launch Local Telegram Automation Bot Mode |
| **`paktool`** | 📦 Alternative Quick Shortcut for PAK Menu |

---

### 2. Direct Headless CLI Commands
Termux shell ya scripts me bina interactive menu khole directly process karne ke liye flags:

```bash
# 📦 Unpack a PAK/OBB file directly
python FeaturesticLeaks.py --unpack /path/to/game.pak

# 📦 Repack an unpacked directory
python FeaturesticLeaks.py --repack /path/to/unpacked_folder

# 🌙 Compile a Lua script to bytecode (.luac)
python FeaturesticLeaks.py --lua-compile /path/to/script.lua

# 🌙 Decompile a bytecode file to source (.lua)
python FeaturesticLeaks.py --lua-decompile /path/to/script.luac

# 🌙 Auto-repair Lua 5.1 syntax errors
python FeaturesticLeaks.py --lua-fix /path/to/script.lua

# 🤖 Ask OpenCode AI via CLI
python FeaturesticLeaks.py --ai "How to inject custom Lua into PUBG Mobile PAK?"
```

---

## 📂 Category-Wise Modular Menu Architecture

Tool visual layout clean, high-performance structured menus me organized hai:

```text
⚡ FEATURESTIC LEAKS v2.8 MAIN MENU
├── [1] 🤖 AI Assistant & Modder     --> Function scanner, custom mod generator & live chat
├── [2] 📦 PAK Tools                 --> Unpack, Repack, Replace, Inject, Skin Swapper, OBB Manager
├── [3] 🌙 LUA Tools                 --> Compile, Decompile, 1-Click Auto Workflow, Obfuscator, Merger
├── [4] 🔑 OpenCode API & Settings   --> Multi-Key auto-rotation, custom endpoint & Telegram bot config
├── [5] 🛠️ Utilities & Help          --> UE4 tools, File Resizer, URL Patcher, Shortcuts & Beginner FAQ
├── [U] 🚀 Auto-Update               --> 1-Touch GitHub update check, backup & auto-restart
└── [0] ✗ EXIT                       --> Close application
```

---

## 🤖 AI Assistant & Modder Engine (Category [1])

```text
🤖 AI ASSISTANT & MODDER MENU
├── [1] 🧠 AI Function Scanner & Modder
│       └── Unpacked folder/file ko scan karta hai, functions, hooks, tables & parameters extract
│           karta hai aur user ke demand par custom Lua 5.1 Game mod script generate karta hai!
├── [2] 👁️💬 AI Interactive Chat & Watch Assistant
│       └── Live File Watcher + AI Chat Assistant! Voice/text commands se real-time auto-unpack,
│           compile aur interactive modding help provide karta hai!
├── [3] 🔑 OpenCode API & Keys Settings
│       └── Multi-Key management (Auto-Rotation), Custom Endpoint & Developer Telegram Bot setup.
└── [0] ↩️ Back to Main Menu
```

---

## 📂 Clean Workspace Directory Structure

Tool launch hote hi aapke SDCard (`/sdcard/FeaturesticLeaks/`) me structured clean folders auto-create ho jaate hain:

```text
/sdcard/FeaturesticLeaks/
├── 📦 PAK_WORKSPACE/            <-- Everything related to PAK & OBB Modding
│   ├── 📥 1_PAK_INPUT/          <-- Original game .pak / .obb files yahan daalo
│   ├── 📂 2_UNPACK/             <-- Extracted folders & assets
│   ├── ✏️ 3_REPLACE/            <-- Edited files yahan daalo for replacement
│   ├── 💉 4_INJECT/             <-- Custom files direct path injection ke liye
│   └── 🚀 5_RESULT/             <-- Final modified .pak & .obb files
│
├── 🌙 LUA_WORKSPACE/            <-- Everything related to Lua Scripting
│   ├── 📜 1_LUA_INPUT/          <-- .lua / .luac files yahan daalo
│   ├── 🔓 2_DECOMPILED/         <-- Decompiled .lua source files
│   ├── ⚙️ 3_COMPILED/           <-- Compiled .luac bytecode files
│   └── 🎉 4_RESULT/             <-- Final processed & merged scripts
│
├── 📁 FOUND_FILES/              <-- Files extracted via Search/Filter tool
├── 📑 DUMP_LOGS/                <-- Security audit reports & memory dumps
└── 📋 LOGS/                    <-- System diagnostic reports & error logs
```

---

## 🧰 Complete Feature Overview

### 📦 1. PAK / OBB Manipulation Engine
* **Multi-Threaded PAK Unpacker**: 32-thread high-speed engine supporting SM4/AES decryption, Zstandard/OBB decompression, and CRC32 stem hash auto-repair.
* **Smart PAK Repacker**: Auto-detects container modes (`MINI_OBB`, `GAMEPATCH`, `OBBZSDIC`) and rebuilds container blocks with byte-exact padding.
* **Replace Existing Files**: Size-independent binary replacer that updates existing assets without header corruption or game crashes.
* **Inject Path (New Files)**: Direct path injector for inserting custom mods into internal game directories (e.g. `Content/Lua/GameLua/Mod/...`). Features built-in Lua 5.1 syntax auto-repair and workspace synchronization.
* **Skin ID Swapper & Asset Dumper**:
  - Swaps Lobby, Ingame, Weapon, Hit Effect & Deadbox skin IDs inside `.uasset` / `.uexp` files.
  - Scans PAK files for textures, meshes, and uassets, exporting raw skin assets with JSON/TXT reports.
* **OBB Manager**: Extract and re-compress OBB containers with exact byte matching.
* **UAsset / UExp Sync Engine**: Auto-pairs companion `.uasset` + `.uexp` files and alerts if asset pairs are broken.

---

### 🌙 2. Lua Master Suite
* **1-Click Auto Lua Workflow**: Scans Lua folders, auto-fixes Lua 5.1 syntax errors, compiles to bytecode, and syncs output to workspace.
* **Universal Compiler & Decompiler**: Converts `.lua` source to `.luac` bytecode and decompiles bytecode back to clean readable Lua.
* **Embed PAK into Lua**: Converts `.pak` into Base64 payload and embeds it directly into a GameGuard Lua script.
* **Universal Pack & Unpack Lua**: Encodes/decodes Lua scripts with standard 8-byte tags (`B64_____`, `XOR_____`, `ZLIB____`, `RAW_____`).
* **Lua String Obfuscator & Dumper**: Encrypts string literals with Hex/Base64/XOR and dumps hidden URLs/IPs.
* **Anti-Bypass & Security Analyzer**: Scans Lua scripts for memory calls, hooks, and bypass signatures with a 0-100 risk score report.
* **Bytecode Header Fixer**: Repairs corrupted magic headers for standard Lua 5.1 (`1B 4C 75 61 51 00...`) or LuaJIT (`1B 4C 4A 02...`).
* **Lua Script Merger**: Combines multiple `.lua` scripts into a modular `Master_Merged_Script.lua` file.

---

### 🤖 3. OpenCode AI Modder & Multi-Key Engine
* **AI Function Scanner & Modder**: Scans unpacked PAK/LUA folders, analyzes function signatures and exports custom GameGuard / Lua 5.1 mod scripts on demand.
* **AI Interactive Watch Assistant**: Real-time voice/text watcher that processes incoming files automatically.
* **Unlimited Multi-Key Rotation**: Supports multiple OpenCode API keys with auto-failover, custom endpoints (`https://api.opencode.ai/v1`), and model selection.
* **Silent Error Recovery**: Smart error classification that filters normal user file issues and reports code bugs cleanly.

---

### 🛠️ 4. Utilities, Diagnostics & Auto-Update
* **UE4 String Tool**: Extract and repack ASCII/Unicode string literals inside `.uasset` / `.uexp` binaries.
* **File Resizer & Equalizer**: Match exact byte size of any PAK, OBB, or LUA file with null-padding.
* **URL & LIB Patcher 🔗**: Find and replace encrypted API endpoints/URLs in `.so` shared libraries.
* **1-Touch GitHub Auto-Updater (`[U]`)**: Checks GitHub for updates, validates syntax, creates backups, and auto-restarts seamlessly.
* **System Diagnostic & Benchmark ⚡**: Live RAM inspection, Lua compiler speed benchmark (ms), and automatic log hygiene.

---

## 🤖 24/7 GitHub Actions Telegram Bot Service

FeaturesticLeaks includes a continuous 24/7 Telegram Bot engine (`bot_runner.py` & `.github/workflows/bot_247.yml`):

### 🚀 Bot Commands:
* `/start` - Bot status & welcome message
* `/help` - View complete command manual
* `/status` - Live workspace file count & memory summary
* `/ai <prompt>` - Ask OpenCode AI modding questions
* `/unpack` - Auto-unpack files in PAK folder
* `/repack` - Repack files from UNPACK folder
* `/lua_compile` - Compile all `.lua` scripts to `.luac`
* `/lua_fix` - Auto-repair Lua 5.1 syntax errors
* `/clean` - Clear temporary workspace files
* `/restart` - Trigger runner loop restart

### 🔧 GitHub Actions Setup:
1. GitHub Repository me jaakar **Settings** -> **Secrets and variables** -> **Actions** kholein.
2. Secrets add karein:
   - `TELEGRAM_BOT_TOKEN`: Bot token from [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID`: Aapka Telegram User ID / Group ID
   - `GH_PAT_TOKEN`: GitHub Personal Access Token (`repo` & `workflow` scopes)
3. Bot 24/7 GitHub Actions par continuously run hota rahega!

### 📱 Running Bot Mode in Termux:
```bash
leak bot
# OR
python3 bot_runner.py
```

---

## 👤 Developer Contact & Community

* 👑 **Main Developer**: [**@L359D**](https://t.me/L359D)
* 📢 **Telegram Channel**: [**t.me/FeaturesticLeaks**](https://t.me/FeaturesticLeaks)
* 🐙 **GitHub Repository**: [**itzgeniusboy/FeaturesticLeaks-Toolkit-**](https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-)
* 💬 **Support**: Direct contact developer on Telegram for VIP mods, keys & inquiries.


