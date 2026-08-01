# 📖 FeaturesticLeaks PAK & LUA Master Suite v2.5 — Official Step-by-Step Guide & Manual (Hinglish)

Is official manual me **FeaturesticLeaks PAK & LUA Master Suite v2.5** ke har ek feature, menu option aur process ko bilkul saral aur detailed Hindi-English (Hinglish) me samjhaya gaya hai.

---

## 👤 Developer & Official Contact
* **Developer Telegram**: [@L359D](https://t.me/L359D) (VIP Developer)
* **Official Telegram Channel**: [https://t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)

---

## ⚡ 1. One-Line Termux Setup & Launch

Termux Terminal kholein, is single command ko copy karke paste karein aur Enter dabayein:

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
   Main menu me **Utilities & Help -> Option 3 (Termux Auto-Setup)** select karein. Iske baad Termux me kahin se bhi sirf yeh type karein:
   ```bash
   leak
   ```

2. **`paktool` Shortcut**:
   ```bash
   paktool
   ```

3. **`run.sh` Launcher**:
   ```bash
   ./run.sh
   ```

---

## 📂 4. SDCard Storage Workspace (`/sdcard/FeaturesticLeaks/`)

Tool launch hote hi aapki internal storage me automatically yeh folders ban jaate hain (ZArchiver me direct dikhenge):

* **`/sdcard/FeaturesticLeaks/PAK/`**: Apni original `.pak` ya `.obb` file yahan rakhein.
* **`/sdcard/FeaturesticLeaks/UNPACK/`**: Unpack ki hui extracted files yahan aayengi.
* **`/sdcard/FeaturesticLeaks/REPLACE/`**: Replacement ke liye edited files ko yahan rakhein.
* **`/sdcard/FeaturesticLeaks/INJECT/`**: Nayi files jo custom path par inject karni hon unhe yahan rakhein.
* **`/sdcard/FeaturesticLeaks/LUA/`**: Plain `.lua` ya compiled `.luac` scripts yahan rakhein.
* **`/sdcard/FeaturesticLeaks/DUMP_LOGS/`**: Audit reports, dumps aur logs yahan save hongi.
* **`/sdcard/FeaturesticLeaks/RESULT/`**: Final modded `.pak`, `.obb`, `.lua`, aur generated scripts yahan milenge.

---

## 🧰 5. Detailed Category & Feature Walkthrough

---

### 📦 CATEGORY 1: PAK / OBB & GAME MODDING TOOLS

#### **[1] Unpack Package (PAK / OBB Extract Karna)**
* **Kya Kaam Karta Hai**:
  Game ke `.pak` ya `.obb` files ko decrypt aur decompress karke pure raw assets (textures, uassets, configs, lua scripts) readable folders me extract karta hai.
* **Step-by-Step Process**:
  1. Apni original `.pak` ya `.obb` file ko `/sdcard/FeaturesticLeaks/PAK/` folder me rakhein.
  2. Main Menu me `1` (PAK / OBB & Game Modding Tools) press karein.
  3. Option `1` (Unpack Package) select karein.
  4. Tool automatic `/sdcard/FeaturesticLeaks/PAK/` scan karke files ki list dikhayega.
  5. Apni file ka index number (jaise `1`) enter karein.
  6. Extraction complete hone par saari files `/sdcard/FeaturesticLeaks/UNPACK/<pak_name>/` folder me mil jayengi.

---

#### **[2] Repack & Inject Tools (3 Advanced Sub-Modes)**
Option `2` chunte hi aapko 3 Modes milenge:

* **Mode 1: Repack Full Workspace (REPACK Folder)**:
  - **Process**: Pehle Option 1 se unpack karein, `UNPACK/<pak_name>/` me changes karein. Phir Option `2` -> `1` chuniye. Tool auto-detect karega ki file `MINI_OBB`, `GAMEPATCH`, ya `OBBZSDIC` mode me compressed hai aur clean `.pak` / `.obb` file `/sdcard/FeaturesticLeaks/RESULT/` me build kar dega.
* **Mode 2: Replace Edited Files (Replace Mode)**:
  - **Process**: Poori pak unpack kiye bina fast & safe editing ke liye! Original `.pak` ko `PAK/` folder me rakhein aur modified files ko `/sdcard/FeaturesticLeaks/REPLACE/` me. Option `2` -> `2` select karein. Tool index hash aur offsets rebuild karke size-independent replace karke result generate kar dega.
* **Mode 3: Inject Files to Custom Target Path (Path Injector)**:
  - **Process**: Nayi files ko PAK container ke andar specific internal path par inject karne ke liye! Source files ko `/sdcard/FeaturesticLeaks/INJECT/` me rakhein. Option `2` -> `3` chuniye aur target internal path (e.g. `Content/Lua/GameLua/Mod/BRMod/Gameplay/Core` ya `ShadowTrackerExtra/Saved/Paks`) paste karein. Tool 100% login-stuck & crash-proof file inject kar dega.

---

#### **[3] One-Click Game Mods**
* **Sub-Option 1: White Body & Gear Asset Nuller**:
  - Character skin mesh aur gear textures ko one-click white body mod me convert karta hai.
* **Sub-Option 2: Skin ID Swapper**:
  - Game ke `.uasset` / `.uexp` binary files me Lobby, Ingame, Weapon, Hit Effect, Deadbox skin IDs ko bina hex editor khole swap karta hai. Option `2` chuniye, Category select karein, aur Original ID aur Target ID enter karein.

---

#### **[4] OBB Manager (Byte-Exact Size Padding)**
* **Kya Kaam Karta Hai**: `.obb` archives ko extract karta hai aur editing ke baad rezip karte waqt exact original byte-size maintaining size padding add karta hai (jisse size check error ya game crash bilkul nahi hota).
* **Process**:
  1. `1` (Unzip OBB) select karke extract karein aur edit karein.
  2. `2` (Rezip OBB) select karein. Tool automatically byte padding add karke original file size match kar dega.

---

#### **[5] PAK Compare & Dump**
* **Process**:
  1. **Compare 2 PAKs**: Do `.pak` files ko compare karke added, removed aur modified files ka exact difference dikhata hai.
  2. **PAK Index / Offset / Hash Dump**: PAK file ke internal structure, offsets, hashes aur encryption details ko `DUMP_LOGS/Dump_<pak_name>.txt` me export kar deta hai.

---

### 🌙 CATEGORY 2: LUA MASTER SUITE

#### **[1] Decompile & Fix Lua**
* **Kya Kaam Karta Hai**: Game ke compiled `.luac` bytecode ko human-readable `.lua` source code me decompile karta hai aur corrupted bytecode headers ko auto-fix karta hai.
* **Process**: File ko `/sdcard/FeaturesticLeaks/LUA/` me rakhein, Option `2` -> `1` select karein.

#### **[2] Compile Lua Source**
* **Kya Kaam Karta Hai**: Plain `.lua` text code ko fast execution `.luac` bytecode file me convert karta hai.
* **Process**: Option `2` -> `2` chuniye aur source `.lua` file select karein. Output `RESULT/` me mil jayega.

#### **[3] Merge & Create GG Menu (Lua Script Merger)**
* **Kya Kaam Karta Hai**: Multiple `.lua` scripts ko modular `do...end` blocks me combine karke ek single master GameGuard Menu Studio script me convert karta hai.
* **Process**: Saari `.lua` files ko `/sdcard/FeaturesticLeaks/LUA/` me rakhein aur Option `2` -> `3` chuniye. Final merged script `/sdcard/FeaturesticLeaks/RESULT/Master_Merged_Script.lua` me ban jayegi.

#### **[4] PAK & Lua Installer Tool**
* **Sub-Option 1 (Embed PAK into Lua Installer)**:
  - `.pak` file ko Base64 encode karke GG Lua script ke andar embed kar deta hai jo run karne par direct PAK target folder me install kar deta hai.
* **Sub-Option 2 (Extract PAK Payload from Lua Script)**:
  - Base64/Hex embedded GG Lua installer script me se original PAK file extract kar leta hai.

#### **[5] Universal Lua Packer & Unpacker**
* **Sub-Option 1 (Unpack Tagged Lua File)**:
  - 8-byte magic tag (`B64_____`, `XOR_____`, `ZLIB____`, `RAW_____`) ko auto-detect karke encrypted script ko unpack karta hai.
* **Sub-Option 2 (Pack Lua File)**:
  - Script ko custom 8-byte tag se encrypt/pack karta hai.

#### **[6] Security & Protection**
* **Sub-Option 1 (String Obfuscator & Dumper)**:
  - Script ke sabhi string literals ko Hex/Base64/XOR me encode karta hai, aur report me URLs, IP addresses, memory offsets (0x...) dump karta hai.
* **Sub-Option 2 (Anti-Bypass Security Audit)**:
  - Script me GameGuard calls (`gg.searchNumber`, `gg.editAll`), clearance hooks aur security risks scan karke 0-100 risk score matrix report generate karta hai.
* **Sub-Option 3 (Bytecode Header Fixer)**:
  - Corrupted magic headers (Lua 5.1 / 5.3 / LuaJIT) ko repair karta hai.

#### **[7] Minifier & GG Code Studio**
* **Sub-Option 1 (Lua Script Optimizer / Minifier)**:
  - Unnecessary comments aur extra spaces strip karta hai, file size reduce karta hai aur pre-flight syntax check (`if`, `function`, `end` balance) karta hai.
* **Sub-Option 2 (GG Memory Code Generator)**:
  - Search & Edit, Freeze Values, Speedhack Toggle, aur Anti-Cheat Stealth Log Cleaner ke production-ready Lua code snippets automatic generate karke `RESULT/` me save kar deta hai.

---

### 🛠️ CATEGORY 3: UTILITIES & HELP

#### **[1] UE4 String Tool**
* `.uasset` / `.uexp` binary files me se text strings dump karta hai aur modify karke wapas repack karta hai.

#### **[2] File Finder**
* PAK workspace ya folders me keyword dwara target files search karta hai.

#### **[3] Termux Auto-Setup**
* Termux terminal me `leak` shortcut command configure karta hai.

#### **[4] Cleanup Workspace**
* Extra temporary working folders ko delete karke storage space clear karta hai.

---

## ❓ Common FAQs & Troubleshooting

### **Q1: `Padding is incorrect` error aata tha pehle?**
* **Answer**: Tool me ab auto-fallback unpad mechanism implement ho chuka hai, ab kisi bhi PAK unpack me padding error nahi aayega!

### **Q2: File list me meri `.lua` ya `.pak` file nahi dikh rahi?**
* **Answer**: Apni file ko `/sdcard/FeaturesticLeaks/PAK/` ya `/sdcard/FeaturesticLeaks/LUA/` folder me rakhein, tool us path se auto-scan kar leta hai.

### **Q3: Shortcut command `leak` kaise set karein?**
* **Answer**: Option `3` (Utilities) -> Option `3` (Termux Auto-Setup) chuniye. Iske baad Termux me direct `leak` type karke app launch kar sakte hain.

---

## 👤 Credits & Official Channel

* **Main Developer**: **[@L359D](https://t.me/L359D)** (VIP Developer)
* **Official Telegram Channel**: **[t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Supported Platform**: Termux / Android Linux / Windows / Linux

