# 📖 FeaturesticLeaks PAK Tool v2.0-ULTIMATE — Complete Usage Guide

Is guide me Termux me **FeaturesticLeaks PAK Tool** ko install karne, run karne, aur iske saare 5 modules ko use karne ka poora detail bataya gaya hai.

---

## 🔑 License Key / Password (At Launch)
Jab aap tool launch karenge, to screen par **License Key** poojha jayega:
- **Offline VIP Bypass Active**: Aap koi bhi key daal sakte hain (jaise `VIP`, `123`, `ADMIN`, ya direct **Enter** press kar sakte hain).
- **Instant Unlocked**: Koi online server check ki zaroorat nahi hai, 100% Offline VIP Access hamesha mil jayega.

---

## ⚡ 1. Termux One-Line Quick Setup & Launch

Termux open karein aur is single command ko copy-paste karein:

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python php clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard && python public/FeaturesticLeaks.py
```

---

## 🚀 2. Step-by-Step Manual Commands

Agar aap alag-alag commands chalana chahte hain:

```bash
# Step 1: Termux Home Directory me purana folder delete karein
cd ~ && rm -rf FeaturesticLeaks-Toolkit-

# Step 2: System Packages & Python Install karein
pkg update -y && pkg install -y git python php clang libffi zlib make nano

# Step 3: Required Python Modules Install karein
pip install rich requests pycryptodome zstandard

# Step 4: GitHub Repo Clone karein
git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git

# Step 5: Folder me enter karein
cd FeaturesticLeaks-Toolkit-

# Step 6: Tool Launch Karein
python public/FeaturesticLeaks.py
```

---

## 🛠️ 3. Main Menu & Module Usage Details

Jab tool launch hoga, aapko 6 modules milenge:

### 📦 [1] Unpack PAK File (Extract UE / Game Asset Archives)
- **Kaise Use Karein**:
  1. Apni target `.pak` file ko Termux folder `pak/original/` me copy karein.
  2. Main Menu me `1` press karein.
  3. Apni `.pak` file ka number select karein.
  4. Extracted files `pak/results/unpack/<file_name>_extracted/` folder me save ho jayengi.

### 🔨 [2] Repack PAK File (Re-build Modified PAK Archive)
- **Kaise Use Karein**:
  1. Modded asset files ko `pak/results/unpack/` ke andar edit karein.
  2. Main Menu me `2` press karein.
  3. Select karein kis folder ko dubara `.pak` me convert karna hai.
  4. Modified `.pak` file `pak/results/repack/` me save ho jayegi.

### 📜 [3] Decompile Lua Script (LuaJIT Bytecode -> Readable Code)
- **Kaise Use Karein**:
  1. Target `.luac` ya `.lua` compiled bytecode file ko `lua/original/` folder me rakhein.
  2. Main Menu me `3` press karein.
  3. File select karke decompile karein.
  4. Readable source code `lua/decompiled/` folder me `.lua` file ke roop me save ho jayega.

### ⚙️ [4] Compile Lua Script (Source Code -> Bytecode)
- **Kaise Use Karein**:
  1. Edit ki hui `.lua` file ko `lua/decompiled/` folder me rakhein.
  2. Main Menu me `4` press karein.
  3. File select karke compile karein.
  4. Output compiled file `lua/compiled/` me `.luac` format me milegi.

### 🗜️ [5] ZIP / APK / OBB Extractor (Archive Utility)
- **Kaise Use Karein**:
  1. Target `.zip`, `.apk`, ya `.obb` archive ko `zip/output/` folder me rakhein.
  2. Main Menu me `5` press karein aur extract option chunein.
  3. Files `zip/extracted/` directory me extract ho jayengi.

### ℹ️ [6] System Info & HWID Inspector
- View device hardware fingerprint, Python version, and offline VIP subscription status.

---

## 🚨 Troubleshooting Common Errors

### Error 1: `python: can't open file 'FeaturesticLeaks.py': No such file or directory`
- **Solution**: FeaturesticLeaks.py file `public/` folder ke andar hai.
- Is command se chalayein:
  ```bash
  python public/FeaturesticLeaks.py
  ```
  ya file copy karein main folder me:
  ```bash
  cp public/FeaturesticLeaks.py . && python FeaturesticLeaks.py
  ```

### Error 2: `pip install pip is forbidden (termux)`
- **Solution**: Pip upgrade skip karein, direct libraries install karein:
  ```bash
  pip install rich requests pycryptodome zstandard
  ```

### Error 3: `Permission Denied`
- Executable permission dein:
  ```bash
  chmod +x run.sh public/FeaturesticLeaks.py
  ```
