# ⚡ FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE

> **Termux / Android Game Reverse Engineering & PAK Manipulation Toolkit**  
> Complete high-performance reverse engineering suite for unpacking, repacking, path-injecting, and rebuilding Unreal Engine / Tencent `.pak` and `.obb` containers natively on Termux / Android.

---

## 👤 Developer & Official Credits

* **Developer Telegram**: [@L359D](https://t.me/L359D)
* **Official Telegram Channel**: [https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)
* **Tool Version**: `FeaturesticLeaks PAK Tool v2.0-ULTIMATE`
* **Supported Platform**: Termux / Android Linux / PC

---

## 🚀 Termux Installation & Quick Start

Termux open karke is one-line command ko copy-paste karke Enter dabayein:

### ⚡ Express One-Line Command (Fresh Setup & Launch)

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard pytz gmalg && python FeaturesticLeaks.py
```

📖 **Detailed Guide**: Sabhi options aur complete workflow sikhne ke liye **[HOW_TO_USE.md](./HOW_TO_USE.md)** dekhein.

---

## 🛠️ Step-by-Step Manual Setup

Agar aap har command ek-ek karke run karna chahte hain:

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

Aap tool ko kisi bhi location se launching shortcuts dwara chala sakte hain:

1. **`leak` Command** (Global Termux Shortcut):
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

## 📁 Automatic Directory Hierarchy

Tool run hote hi local repository aur SDCard (`/sdcard/FeaturesticLeaks/`) me automatic workspace ban jata hai:

```text
FeaturesticLeaks-Toolkit-/
├── FeaturesticLeaks.py       <-- Main Termux Python Tool
├── run.sh                    <-- Shell Auto-Launcher
├── setup.sh                  <-- Termux Shortcut & Folder Setup
├── verify.php                <-- Optional License API
├── README.md                 <-- Tool Summary & Credits
├── HOW_TO_USE.md             <-- Detailed Step-by-Step Manual
│
├── PAK/                      <-- Original .pak / .obb files rakhein
├── UNPACK/                   <-- Extracted files & debug logs
├── REPACK/                   <-- Repack workspace
├── RESULT/                   <-- Final modded .pak / .obb output
│
└── PAK TOOL/                 <-- Path Injector Workspace
    ├── PAK/                  <-- Target .pak files
    ├── EDIT/                 <-- Modified assets to replace/inject
    ├── UNPACK/               <-- Sub-unpack output
    └── RESULT/               <-- Final output PAK
```

> 💡 **SDCard Storage Shortcut**: Files ko aap direct `/sdcard/FeaturesticLeaks/` ke subfolders (`PAK`, `REPLACE`, `INJECT`, `RESULT`) me bhi rakh kar process kar sakte hain.

---

## 🧰 Core Capabilities & Features

### 📦 1. PAK / OBB Tools
1. **Unpack All Types PAKs**: Decrypts SM4/AES crypts, decompresses Zstandard / OBB compression, and outputs extracted files with detailed debug logs.
2. **Repack All Types PAKs**: Auto-detects container modes (`MINI_OBB`, `GAMEPATCH`, `OBBZSDIC`) and rebuilds container blocks cleanly.
3. **Replace Existing Files**: Replaces existing PAK files regardless of file size differences without crash or header corruption issues.
4. **Inject Path (New Files)**: Injects brand new files/folders directly into target internal paths (e.g. `Content/Lua/GameLua/Mod/...`).
5. **White Body Mod**: One-click character asset nuller tool.
6. **Skin ID Swap**: Swaps Lobby, Ingame, Weapon, Hit Effect & Deadbox skin IDs inside `.uasset` / `.uexp` binaries.
7. **OBB Manager**: Unzips OBB containers and rezips with byte-exact padding to match original file sizes.

### 🌙 2. Lua Bytecode Tools
1. **Compile Lua**: Converts `.lua` source code into `.luac` bytecode.
2. **Decompile Lua**: Converts `.luac` bytecode back to readable `.lua` source text.

### 🛠️ 3. Utilities & Help
1. **UE4 String Tool**: Extract and repack readable string literals inside `.uasset` / `.uexp` binary files.
2. **File Finder**: Search files inside PAK structure by keyword or extension.
3. **Termux Auto-Setup**: Configures `leak` global terminal command and SDCard directories automatically.
4. **Workspace Cleanup**: Easily clear temporary working folders to free up storage space.

---

## 👤 Developer Contact & Credits

* **Main Developer**: **[@L359D](https://t.me/L359D)**
* **Official Telegram Channel**: **[t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Platform**: Termux / Android Linux / Windows / Linux
