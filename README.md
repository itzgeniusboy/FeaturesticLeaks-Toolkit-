# FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE ⚡

> **Termux / Linux Android Asset Reverse Engineering & Security Toolkit**  
> Complete reverse engineering suite for extracting, repacking, compiling LUA scripts, compressing ZIP assets, and injecting modded PAK containers on Termux / Android.

---

## 🚀 Termux Installation Commands (Step-by-Step)

Termux me tool setup aur chalane ke liye niche diye gaye commands run karein:

### ⚡ Express One-Line Command (Wipe & Fresh Install)
Termux open karein aur is poori line ko copy-paste kar dein (yeh purana folder delete karke fresh clone aur execute karega):

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python php clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard && python FeaturesticLeaks.py
```

---

### 🛠️ Step-by-Step Commands (Har Step Alag Se Run Karein)

#### **Step 1: Purana Folder Delete Karein (If Exists)**
```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit-
```

#### **Step 2: Termux System Packages Install Karein**
```bash
pkg update -y && pkg install -y git python php clang libffi zlib make nano
```

#### **Step 3: Required Python Libraries Install Karein**
```bash
pip install rich requests pycryptodome zstandard
```

#### **Step 4: GitHub Se Toolkit Clone Karein**
```bash
git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git
```

#### **Step 5: Project Folder Me Enter Karein (IMPORTANT)**
```bash
cd FeaturesticLeaks-Toolkit-
```

#### **Step 6: Main Python Tool Run Karein**
```bash
python FeaturesticLeaks.py
```

---

### 💡 Direct One-Line Execution (Folder Me Hone Par)
Jab aap pehle se `FeaturesticLeaks-Toolkit-` folder me ho:
```bash
python FeaturesticLeaks.py
```

---

## 🔓 100% Offline Bypass Mode

Yeh tool **100% Offline Mode** me chalne ke liye configured hai:
* **No Server/Network Required:** Koi PHP panel ya internet connection ki zaroorat nahi hai.
* **Accept Any Key:** Login screen par aap **koi bhi key** ya string enter karenge, yeh aapko turant **VIP Access** grant kar dega.
* **Dashboard Stats:**
  - **Status:** `ACTIVE VIP`
  - **Expiry:** `31-12-2026`
  - **Days Left:** `999 Days`
  - **HWID:** `LOCAL-DEVICE`

---

## 📂 Automatic Directory Hierarchy

Termux me script run hone par yeh folders automatic create ho jaate hain:

```text
├── pak/
│   ├── original/         <-- Place your target .pak files here
│   └── results/
│       ├── unpack/       <-- Extracted PAK assets output
│       └── repack/       <-- Repacked PAK containers output
├── lua/
│   ├── original/         <-- Uncompiled .lua source scripts
│   ├── compiled/         <-- Compiled bytecodes (.luac)
│   └── decompiled/       <-- Decompiled source code output
├── zip/
│   ├── extracted/        <-- Unzipped asset files
│   └── output/           <-- Compressed .zip archives
└── injector/
    ├── backup/           <-- Safety backups of PAK containers (.bak)
    └── target/           <-- Injection workspace
```

---

## 🧰 Core Modules & Capabilities

1. **[1] PAK TOOL:**
   - **Unpack PAK:** Extracts compressed assets (`zstandard`) and cryptographic headers (`AES-256-GCM`).
   - **Repack PAK:** Re-compresses modified folders into encrypted `.pak` archives with valid magic headers (`0x5E6F7A8B`).
   - **PAK Header Inspector:** Analyzes magic bytes, compression algorithms, and index offsets.

2. **[2] ZIP TOOL:**
   - **Decompress ZIP:** Extracts zip archives to `zip/extracted/`.
   - **Compress Directory:** Zips folders into `zip/output/asset_pack.zip`.

3. **[3] LUA TOOL:**
   - **Lua Compiler:** Compiles source `.lua` files into bytecodes using `luac`.
   - **Lua Decompiler:** Converts bytecodes back to readable `.lua` scripts using `unluac`.
   - **XOR Obfuscator:** Encrypts Lua strings with XOR/Base64 wrappers.

4. **[4] PAK INJECTOR:**
   - **Backup Creator:** Generates safe `.bak` file before patching.
   - **Bytecode Injector:** Injects modded assets and recalculates container offset tables.
   - **Backup Restorer:** Restores original PAK file instantly if needed.

---

## 🌐 PHP Backend Integration (`verify.php`)

Agar aap future me apna khud ka Online Key Verification Panel host karna chahte hain:
1. `verify.php` ko apne web host / VPS / CPanel par upload karein.
2. `verify.php` internal `keys_db.json` database manage karta hai jisse keys create, validate, aur HWID lock hoti hain.
3. `FeaturesticLeaks.py` me `API_ENDPOINT = "http://your-domain.com/verify.php"` set karein.

---

## 👤 Author & Support
* **Tool Name:** FeaturesticLeaks PAK Tool v2.0-ULTIMATE
* **Platform:** Termux / Android Linux
* **UI Theme:** Cyberpunk Neon Green (Rich Terminal Library)
