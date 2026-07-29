# FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE ⚡

> **Termux / Linux Android Game Reverse Engineering & PAK Manipulation Toolkit**  
> Complete high-performance reverse engineering suite for unpacking, repacking, path-injecting, and rebuilding Unreal Engine / Tencent `.pak` and `.obb` containers natively on Termux / Android.
>
> **Tool Name**: `FeaturesticLeaks PAK Tool v2.0`

---

## 🚀 Termux Installation & Quick Start

Termux me tool setup aur run karne ke sabse easy steps niche diye gaye hain:

### ⚡ Express One-Line Command (Wipe & Fresh Launch)
Termux open karke is poori line ko copy-paste karein (yeh old repository clean karke fresh setup ke saath launch karega):

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard && python FeaturesticLeaks.py
```

📖 **Detailed Guide**: Sabhi options aur folder structure ke baare me detail janne ke liye [HOW_TO_USE.md](./HOW_TO_USE.md) dekhein.

---

## 🛠️ Step-by-Step Termux Commands

Agar aap har command ek-ek karke run karna chahte hain:

### **Step 1: Old Directory Clear Karein**
```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit-
```

### **Step 2: Termux Packages Install Karein**
```bash
pkg update -y && pkg install -y git python clang libffi zlib make nano
```

### **Step 3: Python Requirements Install Karein**
```bash
pip install rich requests pycryptodome zstandard
```

### **Step 4: Repository Clone Karein**
```bash
git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git
```

### **Step 5: Directory Enter Karein**
```bash
cd FeaturesticLeaks-Toolkit-
```

### **Step 6: Tool Run Karein**
```bash
python FeaturesticLeaks.py
```

---

## 💡 Quick Launch Command
Jab aap pehle se `FeaturesticLeaks-Toolkit-` folder me ho:
```bash
python FeaturesticLeaks.py
```
*Ya phir auto-launcher script se:*
```bash
chmod +x run.sh && ./run.sh
```

---

## 📁 Automatic Directory Hierarchy

Termux me tool run hote hi yeh folders automatically generate ho jaate hain:

```text
FeaturesticLeaks-Toolkit-/
├── FeaturesticLeaks.py       <-- Main Termux Python Tool
├── run.sh                    <-- Shell Launcher Script
├── verify.php                <-- Optional PHP Auth Panel API
├── README.md                 <-- Overview & Setup Guide
├── HOW_TO_USE.md             <-- Detailed Usage Manual
│
├── PAK/                      <-- Original .pak/.obb files paste karein (For Menu 1 & 2)
├── UNPACK/                   <-- Extracted assets & debug logs output
├── REPACK/                   <-- Structured workspace for repacking
├── RESULT/                   <-- Final repacked .pak files output
│
└── PAK TOOL/                 <-- Path Injector Workspace (For Menu 3 & 4)
    ├── PAK/                  <-- Target .pak files for Option 3 & 4
    ├── EDIT/                 <-- Modified assets or new files to inject
    ├── UNPACK/               <-- Sub-unpack workspace
    └── RESULT/               <-- Final injected .pak output
```

---

## 🧰 Core Main Menu Features

1. **[1] UNPACK ALL TYPES PAKS**
   - Unpacks Unreal Engine, Tencent, GamePatch, & Mini OBB containers.
   - Decrypts SM4/AES crypts and handles Zstandard decompression.
   - Saves output in `UNPACK/` and creates a detailed `Debug_<pak_name>.log`.

2. **[2] REPACK ALL TYPES PAKS**
   - Auto-detects container mode (`MINI_OBB`, `GAMEPATCH`, `OBBZSDIC`).
   - Re-compresses modified assets with block-by-block progress displays.
   - Saves final archive in `RESULT/`.

3. **[3] REPACK ANY SIZE (EXISTING FILES)**
   - Replaces existing files inside `.pak` regardless of file size differences.
   - Uses files from `PAK TOOL/EDIT/` and replaces matching items in `PAK TOOL/PAK/`.
   - Prevents header corruptions and game crashes.

4. **[4] REPACK TO PATH (NEW FILES)**
   - Injects brand new files/folders directly to any specified internal path inside the `.pak` (e.g. `Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`).
   - 100% game compatible logic — guarantees no login stuck or crash issues.

5. **[5] DELETE FOLDER**
   - In-app utility to clean up temporary working folders and free Termux storage.

---

## 🌐 Optional PHP Verification API (`verify.php`)

Agar aap online license management system rely karna chahte hain:
1. `verify.php` ko apne web server / CPanel par host karein.
2. Script user authentication and HWID binding manage karti hai.

---

## 👤 Credits & Support
* **Tool Name**: `FeaturesticLeaks PAK Tool v2.0`
* **Platform**: Termux / Android Linux
