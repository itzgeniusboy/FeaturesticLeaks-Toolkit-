# 📖 FeaturesticLeaks PAK & LUA Master Suite v2.7 — Official Step-by-Step Guide & Manual (Hinglish)

Is official manual me **FeaturesticLeaks PAK & LUA Master Suite v2.7** ke har ek feature, menu option aur process ko bilkul saral aur detailed Hindi-English (Hinglish) me samjhaya gaya hai.

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

## 💡 3. Quick Launch Shortcuts & Tool Auto-Update

Tool ko baar-baar poora path likhe bina launch aur update karne ke liye Termux shortcuts:

1. **`leak` Shortcut** (Main Category Menu):
   ```bash
   leak
   ```

2. **Category Direct Termux Shortcuts**:
   ```bash
   leak pak     # Direct PAK & OBB Tools Sub-Menu
   leak lua     # Direct LUA Master Suite Sub-Menu
   leak watch   # Direct Watch Mode Engine
   leak ai      # Direct AI Tools & API Key Manager
   leak utils   # Direct Utilities & Setup Sub-Menu
   leak update  # Direct Auto-Updater Check
   ```

3. **`paktool` Shortcut**:
   ```bash
   paktool
   ```

4. **🚀 Instant Update & Banner System**:
   - Tool start hote hi background me automatically GitHub check karta hai. Agar koi update milta hai, toh banner notification screen par dikhta hai.
   - Main menu me **`U`** dabayein ya **Utilities Menu -> Option [9] Check Tool Update** chunien. Tool update download karke, syntax verify karega, `.py.bak` backup create karega, aur auto-restart ho jayega.

---

## 📂 4. Clean & Organized Workspace (`/sdcard/FeaturesticLeaks/`)

Tool launch hote hi aapki internal storage me automatically yeh structured folders ban jaate hain (ZArchiver me direct bilkul clean dikhenge):

### 📦 **`PAK_WORKSPACE/`** (PAK & OBB Modding Workspace)
* **`1_PAK_INPUT/`**: Apni original `.pak` ya `.obb` file yahan rakhein.
* **`2_UNPACK/`**: Unpack ki hui extracted files aur assets yahan aayengi.
* **`3_REPLACE/`**: Size-independent replacement ke liye edited files yahan rakhein.
* **`4_INJECT/`**: Target path injection ke liye custom files yahan rakhein.
* **`5_RESULT/`**: Final repacked `.pak` aur `.obb` files yahan save hongi.

### 🌙 **`LUA_WORKSPACE/`** (Lua Scripts Modding Workspace)
* **`1_LUA_INPUT/`**: Plain `.lua` ya compiled `.luac` scripts yahan rakhein.
* **`2_DECOMPILED/`**: Decompiled readable `.lua` source files yahan milenge.
* **`3_COMPILED/`**: Compiled `.luac` bytecode files yahan save honge.
* **`4_RESULT/`**: Final processed, auto-fixed aur merged master scripts yahan milenge.

---

## 💡 UAsset & UExp Double File Concept (Important Note)

Unreal Engine 4 (UE4) me har asset ke do hisse hote hain:
1. **`.uasset`**: Asset ka Header aur Metadata (Object structure, paths, class refs).
2. **`.uexp`**: Asset ka actual Raw Binary Data (Texture payloads, Mesh data, Sound buffers, Strings).

⚠️ **Game Engine Requirement**: Game me asset tabhi load hota hai jab **`.uasset` aur `.uexp` dono bilkul same folder me aur same filename ke sath rahein**. Agar ek bhi file missing hogi toh game crash ho jayega ya black texture aayega.

🔥 **FeaturesticLeaks Smart Pairing**: Jab bhi aap tool me koi file pick karte hain:
- Tool automatic companion file (`.uexp` for `.uasset` or vice-versa) search karke link kar deta hai.
- Agar companion file missing hoti hai, toh warning badge dikhata hai taaki game crash na ho!
- List me `[F]` option press karke aap keyword se instantly target file search/filter kar sakte hain!

---

## 🧰 5. Detailed Category & Feature Walkthrough

---

### 📦 CATEGORY 1: PAK / OBB & GAME MODDING TOOLS

#### **[1] Unpack Package (Multi-Threaded PAK/OBB Extract Engine)**
* **Kya Kaam Karta Hai**:
  Game ke `.pak` ya `.obb` files ko decrypt (SM4/AES) aur decompress (Zstandard/OBB) karke pure raw assets extract karta hai.
  Multi-threaded acceleration (32 parallel threads tak) se extraction super fast hota hai. Corrupted stem CRC32 files ko automatically repair kar deta hai.
* **Step-by-Step Process**:
  1. Apni original `.pak` ya `.obb` file ko `/sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT/` folder me rakhein.
  2. Main Menu me `1` (PAK / OBB & Game Modding Tools) press karein.
  3. Option `1` (Unpack Package) select karein.
  4. Tool automatic input folder scan karke files ki list dikhayega. Keyword search ke liye `F` press kar sakte hain.
  5. Apni file ka index number (jaise `1`) enter karein.
  6. Extraction complete hone par saari files `/sdcard/FeaturesticLeaks/PAK_WORKSPACE/2_UNPACK/<pak_name>/` folder me mil jayengi.

---

#### **[2] Repack & Inject Tools (3 Advanced Sub-Modes)**
Option `2` chunte hi aapko 3 Modes milenge:

* **Mode 1: Repack Full Workspace**:
  - **Process**: Pehle Option 1 se unpack karein, `2_UNPACK/<pak_name>/` me changes karein. Phir Option `2` -> `1` chuniye. Tool auto-detect karega ki file `MINI_OBB`, `GAMEPATCH`, ya `OBBZSDIC` mode me compressed hai aur clean `.pak` / `.obb` file `5_RESULT/` me build kar dega.
* **Mode 2: Replace Existing Files (Replace Mode)**:
  - **Process**: Poori pak unpack kiye bina fast & safe editing ke liye! Original `.pak` ko `1_PAK_INPUT/` me rakhein aur modified files ko `3_REPLACE/` me. Option `2` -> `2` select karein. Tool index hash aur offsets rebuild karke size-independent replace karke result generate kar dega.
* **Mode 3: Inject Files to Custom Target Path (Path Injector)**:
  - **Process**: Nayi files ko PAK container ke andar specific internal path par inject karne ke liye! Source files ko `4_INJECT/` me rakhein. Option `2` -> `3` chuniye aur target internal path (e.g. `Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`) paste karein. Tool 100% login-stuck & crash-proof file inject kar dega.

---

#### **[3] One-Click Game Mods**
* **Sub-Option 1: White Body & Gear Asset Nuller**:
  - Character skin mesh aur gear textures ko one-click white body mod me convert karta hai.
* **Sub-Option 2: Skin ID Swapper & Asset Dumper**:
  - Game ke `.uasset` / `.uexp` binary files me Lobby, Ingame, Weapon, Hit Effect, Deadbox skin IDs ko bina hex editor khole swap karta hai.
  - Skin Assets Dumper PAK ya UNPACK folders se skin meshes aur textures scanning karke report aur assets export karta hai.

---

#### **[4] OBB Manager (Byte-Exact Size Padding)**
* **Kya Kaam Karta Hai**: `.obb` archives ko extract karta hai aur editing ke baad rezip karte waqt exact original byte-size maintaining size padding add karta hai (jisse size check error ya game crash bilkul nahi hota).

---

### 🌙 CATEGORY 2: LUA MASTER SUITE

#### **[1] Decompile & Fix Lua**
* **Kya Kaam Karta Hai**: Game ke compiled `.luac` bytecode ko human-readable `.lua` source code me decompile karta hai aur corrupted bytecode headers ko auto-fix karta hai.
* **Process**: File ko `/sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT/` me rakhein, Option `2` -> `1` select karein. Result `2_DECOMPILED/` me mil jayega.

#### **[2] Compile Lua Source**
* **Kya Kaam Karta Hai**: Plain `.lua` text code ko fast execution `.luac` bytecode file me convert karta hai. Output `3_COMPILED/` me save ho jata hai.

#### **[3] Merge & Create GG Menu (Lua Script Merger)**
* **Kya Kaam Karta Hai**: Multiple `.lua` scripts ko modular `do...end` blocks me combine karke ek single master GameGuard Menu Studio script me convert karta hai. Final script `4_RESULT/Master_Merged_Script.lua` me ban jayegi.

#### **[4] Embed PAK into Lua Installer**
* **Kya Kaam Karta Hai**: PAK file ko Base64 me encode karke direct Lua script me inject karta hai taaki GameGuard bypass script directly memory me load kar sake.

#### **[9] 🤖 AI-Assisted Lua Repair & Multi-API Key Manager**
* **Kya Kaam Karta Hai**:
  - Google Gemini, Groq, aur OpenRouter API AI models ka upayog karke broken/syntax error wale Lua scripts ko automatically scan aur repair karta hai.
  - Multi-API Key Manager system ke dwara aap multiple API keys save kar sakte hain. Jab ek API key limit reach kare gi, toh tool automatically doosri key par switch karke request handle karega!
* **Setup Step**:
  1. Lua Master Suite me Option `9` press karein -> Option `2` (Manage AI API Keys).
  2. Apni Google Gemini API Key (`https://aistudio.google.com`) ya Groq Key (`https://console.groq.com`) paste karein.
  3. Active Provider set karein aur Option `1` (Run AI-Assisted Lua Repair) par click karke kisi bhi broken Lua script ko instantly fix karein!

---

### 🛠️ CATEGORY 3: UTILITIES, DIAGNOSTICS & UPDATES

#### **[1] UE4 String Tool**: `.uasset` / `.uexp` binary files me se text strings dump karta hai aur modify karke wapas repack karta hai.
#### **[2] File Finder**: PAK workspace ya folders me keyword dwara target files search karta hai.
#### **[3] Termux Auto-Setup**: Termux terminal me `leak` shortcut command configure karta hai.
#### **[4] File Resizer & Equalizer**: Kisi bhi PAK, OBB, ya LUA file ka exact byte size match karta hai.
#### **[5] Cleanup Workspace**: Extra temporary working folders ko delete karke storage space clear karta hai.
#### **[6] Check Tool Update 🚀**: GitHub se instant latest update pull karta hai.
#### **[10] Diagnostic & Benchmark ⚡**: Termux RAM usage inspect karta hai, Lua compiler speed (ms) check karta hai, aur old log files clear karta hai.
#### **[8] Watch Mode 👁️**: Input folders ko real-time monitor karta hai. Jaise hi koi naye `.pak` ya `.lua` files drop ki jati hain, yeh unhe automatically unpack ya compile kar deta hai. Shortcuts panel include karta hai (`[1]-[5]`, `[U]`, `[help]`).

---

### 🤖 CATEGORY 4: 24/7 GITHUB ACTIONS TELEGRAM BOT SERVICE

Tool me automated 24/7 Telegram Bot system integrate kiya gaya hai jo GitHub Actions par bina ruke chalta rehta hai:
- **5h 50m Auto-Restart Loop**: GitHub Actions me max 6 hours job limit hoti hai. Script 5 hours 50 minutes (21,000s) par automatically state save karke next workflow run dispatch trigger kar deti hai, jisse bot continuous 24/7 active rehta hai.
- **Auto File Processor**: Telegram bot ko `.pak`, `.obb`, `.lua`, ya `.luac` file bhejte hi tool usko receive karke automatic unpack, fix, aur compile kar deta hai.
- **Bot Commands**:
  - `/status` -> Live workspace status
  - `/ai <query>` -> OpenCode AI engine query
  - `/clean` -> Clean temporary files
  - `/restart` -> Manual runner restart

---

## ❓ Common FAQs & Troubleshooting

### **Q1: Tool ko update kaise karein?**
* **Answer**: Main Menu me **`U`** type karein ya **Utilities & Help -> Option [9] Check Tool Update 🚀** select karein. Tool automatically GitHub se verified update pull karke auto-restart ho jayega.

### **Q2: User dwara file delete karne ke baad bhi same file kyon inject ho rahi thi aur ab kaise fixed hai?**
* **Answer**: Pehle Lua pre-processing option `_fixed51.lua` aur temporary `.tmp_luac` files create karta tha, aur secondary fallback search paths (`INJECT`, `REPLACE`, `LUA`) ke karan agar kisi ek internal folder me purani file bachi hoti thi toh tool usko detect kar leta tha. Ab tool me:
  1. Strict folder isolation apply kar di gayi hai (`REPLACE` sirf replace folders dekhega aur `INJECT` sirf inject folders).
  2. `/sdcard/FeaturesticLeaks/` SDCard folder aur internal workspace folders me automatic deletion synchronization lagayi gayi hai (jab user SDCard se file delete karega toh internal directory se bhi purani file auto-delete ho jayegi).
  3. All temporary `_fixed51.lua` aur `.tmp_luac` files directly in-place update honge aur temporary leftovers script process hotes hi auto-cleanup honge.

### **Q3: File Manager me folders clean kaise rahte hain?**
* **Answer**: Purane bikhre hue folders auto-clean ho chuke hain! Ab sirf do organized main folders **`PAK_WORKSPACE`** aur **`LUA_WORKSPACE`** rahenge, jiske andar numeric sub-folders (`1_PAK_INPUT`, `2_UNPACK`, `3_REPLACE`, `4_INJECT`, `5_RESULT`) honge.

### **Q3: Bug report developer ko kaise jata hai?**
* **Answer**: Tool me automatic bug reporting engine shamil hai jo sirf actual python code errors developer ke Telegram bot par bhejta hai. Normal API rate limits aur user file missing error messages filter ho jaate hain.

---

## 👤 Credits & Official Channel

* **Main Developer**: **[@L359D](https://t.me/L359D)** (VIP Developer)
* **Official Telegram Channel**: **[t.me/FeaturesticLeaks](https://t.me/FeaturesticLeaks)**
* **Supported Platform**: Termux / Android Linux / Windows / Linux

