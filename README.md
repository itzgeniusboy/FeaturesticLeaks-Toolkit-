# ⚡ FEATURESTIC LEAKS PAK & LUA MASTER SUITE v2.5

> **Termux / Android Game Reverse Engineering, PAK Manipulation & Universal Lua Suite**  
> Complete high-performance reverse engineering suite for unpacking, repacking, path-injecting, rebuilding Unreal Engine / Tencent `.pak` & `.obb` containers, dumping skin assets, and managing Lua bytecode natively on Termux, Android Linux, and PC.

---

## 👤 Developer & Official Credits

* **Developer Telegram**: [@L359D](https://t.me/L359D) (VIP Developer)
* **Official Telegram Channel**: [https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)
* **Tool Version**: `FeaturesticLeaks PAK & LUA Master Suite v2.5`
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

### **Step 6: Tool Run Karein**
```bash
python FeaturesticLeaks.py
```

---

## 💡 Quick Launch Shortcuts

Shortcut commands through tool ko Termux me kisi bhi location se launch kar sakte hain:

1. **`leak` Command** (Global Termux Terminal Shortcut):
   ```bash
   leak
   ```
2. **`paktool` Command**:
   ```bash
   paktool
   ```
3. **Auto-Launcher Script**:
   ```bash
   chmod +x run.sh && ./run.sh
   ```

---

## 📁 Automatic Workspace Structure

Tool launch hote hi local folder aur SDCard (`/sdcard/FeaturesticLeaks/`) me automatic workspace paths generate ho jate hain:

```text
FeaturesticLeaks-Toolkit-/
├── FeaturesticLeaks.py       <-- Main Termux Python Tool Engine
├── run.sh                    <-- Shell Auto-Launcher
├── setup.sh                  <-- Termux Shortcut & Folder Setup
├── README.md                 <-- Tool Summary & Credits
├── DOCUMENTATION.md          <-- Complete Step-by-Step Manual
│
├── PAK/                      <-- Original .pak / .obb files yahan rakhein
├── UNPACK/                   <-- Extracted files & debug logs
├── REPLACE/                  <-- Modified files for size-independent replacement
├── INJECT/                   <-- Custom files for direct path injection
├── LUA/                      <-- .lua / .luac scripts for Lua tools
├── DUMP_LOGS/                <-- Skin asset logs & Lua audit reports
├── RESULT/                   <-- Final modded .pak, .obb, .lua & skin dumps output
│
└── PAK TOOL/                 <-- Path Injector Workspace
    ├── PAK/                  <-- Target .pak files
    ├── EDIT/                 <-- Modified assets to replace/inject
    ├── UNPACK/               <-- Sub-unpack output
    └── RESULT/               <-- Final output PAK
```

> 💡 **SDCard Direct Access**: Files ko aap direct `/sdcard/FeaturesticLeaks/` ke subfolders (`PAK`, `UNPACK`, `REPLACE`, `INJECT`, `LUA`, `RESULT`, `DUMP_LOGS`) me rakh kar process kar sakte hain (ZArchiver me direct dikhega).

---

## 🧰 Complete Feature Overview

### 📦 1. PAK / OBB Tools
1. **Unpack All Types PAKs**: Decrypts SM4/AES crypts, decompresses Zstandard / OBB compression, and outputs extracted files with detailed debug logs.
2. **Repack All Types PAKs**: Auto-detects container modes (`MINI_OBB`, `GAMEPATCH`, `OBBZSDIC`) and rebuilds container blocks cleanly.
3. **Replace Existing Files**: Replaces existing PAK files regardless of file size differences without crash or header corruption issues.
4. **Inject Path (New Files)**: Injects brand new files/folders directly into target internal paths (e.g. `Content/Lua/GameLua/Mod/...`).
5. **White Body Mod**: One-click character asset nuller tool.
6. **Skin ID Swap & Skin Asset Dumper**:
   - Swaps Lobby, Ingame, Weapon, Hit Effect & Deadbox skin IDs inside `.uasset` / `.uexp` binaries.
   - **Skin Assets Dumper**: Scans PAK files or UNPACK folders for skin textures, meshes, uassets/uexps, generates `.txt` and `.json` reports, and exports raw skin assets directly to `RESULT/SKINS_DUMP/`.
7. **OBB Manager**: Unzips OBB containers and rezips with byte-exact padding to match original file sizes.

### 🌙 2. Lua Master Suite
1. **Compile Lua**: Converts `.lua` source code into `.luac` bytecode.
2. **Decompile Lua**: Converts `.luac` bytecode back to readable `.lua` source text.
3. **Embed PAK into Lua**: Converts `.pak` into Base64 payload and embeds it directly into a GameGuard Lua installer script.
4. **Universal Pack Lua**: Encodes Lua scripts using extensible plugin architecture with fixed 8-byte ASCII tags (`B64_____`, `XOR_____`, `ZLIB____`, `RAW_____`).
5. **Universal Unpack Lua**: Reads 8-byte magic tag, auto-detects algorithm, and decodes byte-for-byte losslessly.
6. **Lua String Obfuscator & Dumper Engine**:
   - Encrypts all string literals with Hex/Base64/XOR and injects a runtime decoder wrapper.
   - Extracts and dumps all string constants, URLs, IP addresses, and memory offsets into `DUMP_LOGS/`.
7. **Anti-Bypass & Security Analyzer**: Audits Lua scripts for GameGuard memory calls (`gg.editAll`, `gg.searchNumber`), clearance hooks, and security risks with a 0-100 risk score report.
8. **Bytecode Header Fixer & Debug Stripper**: Repairs corrupted magic headers for Lua 5.1 (`1B 4C 75 61 51 00...`) or LuaJIT (`1B 4C 4A 02...`), and strips debug local symbols.
9. **Lua Script Merger**: Merges multiple `.lua` scripts into a clean, modular `Master_Merged_Script.lua` file wrapped in `do...end` blocks.

### 🛠️ 3. Utilities & Help
1. **UE4 String Tool**: Extract and repack readable string literals inside `.uasset` / `.uexp` binary files.
2. **File Finder**: Search files inside PAK structure by keyword or extension.
3. **Termux Auto-Setup**: Configures `leak` global terminal command and SDCard directories automatically.
4. **Workspace Cleanup**: Easily clear temporary working folders to free up storage space.

---

## 👤 Developer Contact & Official Credits

* **Main Developer**: **[@L359D](https://t.me/L359D)**
* **Official Telegram Channel**: **[t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Platform**: Termux / Android Linux / Windows / Linux
