# 📖 FeaturesticLeaks PAK Tool v2.0-ULTIMATE — Complete Termux Usage Manual

Is manual me **FeaturesticLeaks PAK Tool v2.0** ko Termux me setup karne aur iske sabhi features ko step-by-step use karne ka poora tareeka vistaar se bataya gaya hai.

---

## 👤 Developer & Official Contact
* **Developer Telegram**: [@L359D](https://t.me/L359D)
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
   Main menu me **Option 3 -> Option 4 (Termux Auto-Setup)** select karein. Iske baad Termux me kahin se bhi sirf yeh type karein:
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
* **`/sdcard/FeaturesticLeaks/REPLACE/`**: Jo files aap replacement ke liye edit karein unhe yahan rakhein (Option 3 ke liye).
* **`/sdcard/FeaturesticLeaks/INJECT/`**: Nayi files jo custom path par inject karni hon unhe yahan rakhein (Option 4 ke liye).
* **`/sdcard/FeaturesticLeaks/RESULT/`**: Final modded `.pak` ya `.obb` file yahan milegi.

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

#### **[6] Skin ID Swap**
* **Purpose**: `.uasset` / `.uexp` binaries me Lobby, Ingame, Weapon, Hit Effect, Deadbox skin IDs ko aapas me swap karna.
* **Steps**:
  1. Menu me `1` -> `6` select karein.
  2. Category select karein (e.g., Skin Lobby ID Swap).
  3. Original Skin ID (decimal, e.g. `101001`) aur Target Skin ID (decimal, e.g. `101002`) enter karein.
  4. Tool pure workspace me matching hex values swap kar dega.

#### **[7] OBB Manager**
* **Purpose**: OBB archive ko unzip karna aur re-zip karte waqt byte-exact size padding add karna.
* **Steps**:
  1. `1` (Unzip OBB) se `.obb` file extract karein. Isse file ka original size `.ini` file me save ho jata hai.
  2. Editing ke baad `2` (Rezip OBB) select karein. Tool extra byte padding add karke exact original size maintain kar dega.

---

### 🌙 CATEGORY 2: LUA TOOLS

#### **[1] Compile Lua**
* Plain text `.lua` source code file ko `.luac` bytecode file me convert karta hai.

#### **[2] Decompile Lua**
* Game `.luac` bytecode file ko readable `.lua` source text me convert karta hai (luadec / unluac / internal Python Lua engine se).

---

### 🛠️ CATEGORY 3: UTILITIES & HELP

#### **[1] UE4 String Tool**
* `.uasset` aur `.uexp` binary files me se readable text strings extract aur repack karne ke liye.

#### **[2] File Finder**
* Search pattern dwara workspace ke andar target files search karne ke liye.

#### **[3] Workspace Summary & Guide**
* Live file counts, folder sizes aur step-by-step usage tips dekhne ke liye.

#### **[4] Termux Auto-Setup**
* Termux me global `leak` shortcut setup karta hai aur SDCard folders create karta hai.

#### **[5] Cleanup Workspace**
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

* **Developer**: **[@L359D](https://t.me/L359D)**
* **Telegram Channel**: **[https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Platform**: Termux / Android Linux
