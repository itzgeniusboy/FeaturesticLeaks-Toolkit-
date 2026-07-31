# 📖 FeaturesticLeaks PAK & LUA Master Suite v2.5 — Official Documentation & Technical Manual

Is manual me **FeaturesticLeaks PAK & LUA Master Suite v2.5** ko Termux me setup karne aur iske sabhi features ko step-by-step use karne ka poora tareeka vistaar se bataya gaya hai.

---

## 👤 Developer & Official Contact
* **Developer Telegram**: [@L359D](https://t.me/L359D) (VIP Developer)
* **Official Telegram Channel**: [https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)

---

## ⚡ 1. One-Line Termux Setup & Run

Termux Terminal kholein, is poore command ko copy karke paste karein aur Enter dabayein:

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard pytz gmalg && python FeaturesticLeaks.py
```

---

## 🛠️ 2. Step-by-Step Manual Setup

Agar aap ek-ek command alag run karna chahte hain:

```bash
# Step 1: Storage permission maangein
termux-setup-storage

# Step 2: System packages update aur install karein
pkg update -y && pkg install -y git python clang libffi zlib make nano

# Step 3: Required Python libraries install karein
pip install rich requests pycryptodome zstandard pytz gmalg

# Step 4: Repository clone karein
cd ~ && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git

# Step 5: Directory me enter karein
cd FeaturesticLeaks-Toolkit-

# Step 6: Tool launch karein
python FeaturesticLeaks.py
```

---

## 💡 3. Quick Launch Shortcuts

Tool ko baar-baar poora path likhe bina launch karne ke liye:

1. **`leak` Shortcut**:
   Main menu me **Utilities & Help -> Option 4 (Termux Auto-Setup)** select karein. Iske baad Termux me kahin se bhi sirf yeh type karein:
   ```bash
   leak
   ```

2. **`paktool` Shortcut**:
   `run.sh` dwara setup karne ke baad direct:
   ```bash
   paktool
   ```

3. **`run.sh` Launcher**:
   ```bash
   ./run.sh
   ```

---

## 📂 4. SDCard Storage Workspace (`/sdcard/FeaturesticLeaks/`)

Aap Termux ke internal folder ke ilawa direct SDCard / Internal Storage folder se bhi files process kar sakte hain:

* **`/sdcard/FeaturesticLeaks/PAK/`**: Apni original `.pak` ya `.obb` file yahan rakhein.
* **`/sdcard/FeaturesticLeaks/UNPACK/`**: Unpack ki hui output files yahan aayengi.
* **`/sdcard/FeaturesticLeaks/REPLACE/`**: Jo files aap replacement ke liye edit karein unhe yahan rakhein.
* **`/sdcard/FeaturesticLeaks/INJECT/`**: Nayi files jo custom path par inject karni hon unhe yahan rakhein.
* **`/sdcard/FeaturesticLeaks/LUA/`**: Plain `.lua` ya compiled `.luac` scripts yahan rakhein.
* **`/sdcard/FeaturesticLeaks/DUMP_LOGS/`**: Skin asset logs aur Lua security audit reports yahan save hoti hain.
* **`/sdcard/FeaturesticLeaks/RESULT/`**: Final modded `.pak`, `.obb`, `.lua`, aur exported skin assets yahan milenge.

---

## 🧰 5. Detailed Category & Menu Walkthrough

---

### 📦 CATEGORY 1: PAK / OBB TOOLS

#### **[1] Unpack All Types PAKs**
* **Purpose**: Game `.pak` ya `.obb` files ko extract karke assets (textures, Lua scripts, configs) readable form me laana.
* **Steps**:
  1. File ko `PAK/` ya `/sdcard/FeaturesticLeaks/PAK/` me copy karein.
  2. Menu me `1` (PAK / OBB Tools) enter karein, phir `1` (Unpack) select karein.
  3. Screen par dikhne wali list me se file number chuniye.
  4. Script file ko unpack karke `UNPACK/<filename>/` folder me save kar degi.

#### **[2] Repack All Types PAKs**
* **Purpose**: Unpack ki hui edited files ko wapas original container mode me build karna.
* **Steps**:
  1. Pehle Option 1 se unpack karein aur `UNPACK/<filename>/` me changes karein.
  2. Menu me `1` -> `2` (Repack) select karein.
  3. Tool auto-detect karega ki file `MINI_OBB`, `GAMEPATCH`, ya `OBBZSDIC` mode me re-compress honi hai.
  4. Final file `RESULT/` aur `/sdcard/FeaturesticLeaks/RESULT/` me mil jayegi.

#### **[3] Replace Files (Repack Any Size)**
* **Purpose**: PAK container me maujood existing files ko modified files se replace karna (chahe size chota ho ya bada).
* **Steps**:
  1. Original `.pak` file ko `PAK/` folder me rakhein.
  2. Edited file ko `REPLACE/` ya `/sdcard/FeaturesticLeaks/REPLACE/` me rakhein.
  3. Menu me `1` -> `3` (Replace Files) chuniye.
  4. Tool offsets aur index hash rebuild karke crash-free `.pak` file generate kar dega.

#### **[4] Inject Path (Repack To Custom Path)**
* **Purpose**: PAK file me kisi specific internal path par nayi file inject karna.
* **Steps**:
  1. Original `.pak` ko `PAK/` me rakhein aur nayi inject file ko `INJECT/` folder me.
  2. Menu me `1` -> `4` (Inject Path) chuniye.
  3. Game internal path enter karein (e.g. `Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`).
  4. Tool 100% login stuck & crash proof method se file inject kar dega.

#### **[5] White Body Mod**
* **Purpose**: One-click character & gear mesh nuller.
* **Steps**:
  1. Unpack workspace tayar karein.
  2. Menu me `1` -> `5` chuniye aur target character mesh select karke white body mod apply karein.

#### **[6] Skin ID Swap & Skin Assets Dumper**
* **Purpose**:
  - Binary `.uasset`/`.uexp` files me Lobby, Ingame, Weapon, Hit Effect, Deadbox skin IDs swap karna.
  - PAK ya UNPACK workspace se saari skin textures, meshes, aur uassets dump & export karna.
* **Steps**:
  1. Option `6` select karein.
  2. ID Swap ke liye categories 1-5 select karke Original ID aur Target ID enter karein.
  3. Skin Assets Dumper ke liye Option `6` select karein. Tool saari skin files scan karke `.txt` & `.json` logs report generate karega aur Option `2` dabane par saare skin assets `RESULT/SKINS_DUMP/` me export kar dega.

#### **[7] OBB Manager**
* **Purpose**: OBB archive ko unzip karna aur re-zip karte waqt byte-exact size padding add karna.
* **Steps**:
  1. `1` (Unzip OBB) se `.obb` file extract karein. Isse file ka original size `.ini` file me save ho jata hai.
  2. Editing ke baad `2` (Rezip OBB) select karein. Tool extra byte padding add karke exact original size maintain kar dega.

---

### 🌙 CATEGORY 2: LUA MASTER SUITE

#### **[1] Compile Lua**
* Plain text `.lua` source code file ko `.luac` bytecode file me convert karta hai.

#### **[2] Decompile Lua**
* Game `.luac` bytecode file ko readable `.lua` source text me convert karta hai.

#### **[3] Embed PAK into Lua**
* Any `.pak` file ko Base64 payload me stringify karke GameGuard Lua script installer generated code me embed kar deta hai.

#### **[4] Universal Pack Lua**
* Lua file ko standard 8-byte ASCII magic tag ke saath encode karta hai (`B64_____`, `XOR_____`, `ZLIB____`, `RAW_____`).

#### **[5] Universal Unpack Lua**
* Packed file me se 8-byte header auto-read karke, encoding pattern identify karta hai aur lossless unpack karke `.lua` recover karta hai.

#### **[6] String Obfuscator & Dumper Engine**
* **Obfuscate**: Script ke sabhi string literals ko Hex/Base64/XOR me encode karke `_HEX()` runtime decoder wrapper top par inject kar deta hai.
* **Dump**: Script se saari URLs, IP addresses, memory offsets (0x...), aur string constants extract karke `DUMP_LOGS/` me detailed report save karta hai.

#### **[7] Anti-Bypass & Security Analyzer**
* Lua script me GameGuard memory calls (`gg.editAll`, `gg.searchNumber`), clearance hooks, dynamic code execution (`loadstring`), aur byte dumps audit karta hai aur 0-100 risk score matrix ke sath detailed line-by-line audit report generate karta hai.

#### **[8] Bytecode Header Fixer & Debug Stripper**
* Corrupted magic headers ko repair karta hai (Lua 5.1 `1B 4C 75 61 51 00...` ya LuaJIT `1B 4C 4A 02...`), aur debug symbols/local variable names strip karke script size chota karta hai.

#### **[9] Lua Script Merger**
* `LUA/` folder me maujood multiple `.lua` scripts ko scope collision bina kiye modular `do...end` blocks me single `Master_Merged_Script.lua` file me merge kar deta hai.

---

### 🛠️ CATEGORY 3: UTILITIES & HELP

#### **[1] UE4 String Tool**
* `.uasset` aur `.uexp` binary files me se readable text strings extract aur repack karne ke liye.

#### **[2] File Finder**
* Search pattern dwara workspace ke andar target files search karne ke liye.

#### **[3] Termux Auto-Setup**
* Termux me global `leak` shortcut setup karta hai aur SDCard folders create karta hai.

#### **[4] Cleanup Workspace**
* Extra temporary working folders ko delete karke storage space free karta hai.

---

## 🚨 Common Questions & Troubleshooting

### **Q1: `python: can't open file 'FeaturesticLeaks.py'`**
* **Fix**: Ensure karein ki aap right folder me hain:
  ```bash
  cd ~/FeaturesticLeaks-Toolkit- && python FeaturesticLeaks.py
  ```

### **Q2: Permission Denied error on Termux**
* **Fix**: Storage permission re-grant karein:
  ```bash
  termux-setup-storage
  ```

---

## 👤 Credits & Contact

* **Developer**: **[@L359D](https://t.me/L359D)** (VIP Developer)
* **Telegram Channel**: **[https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Platform**: Termux / Android Linux / Windows / Linux
