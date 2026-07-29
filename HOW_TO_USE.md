# 📖 FeaturesticLeaks PAK Tool v2.0-ULTIMATE — Complete Termux Usage Manual

Is manual me Termux me **FeaturesticLeaks PAK Tool** ko setup karne aur iske saare features ko step-by-step use karne ka tareeka bataya gaya hai.

---

## ⚡ 1. Termux One-Line Installation & Run

Termux Terminal kholein aur yeh command paste karke Enter dabayein:

```bash
cd ~ && rm -rf FeaturesticLeaks-Toolkit- && pkg update -y && pkg install -y git python clang libffi zlib make nano && git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git && cd FeaturesticLeaks-Toolkit- && pip install rich requests pycryptodome zstandard && python FeaturesticLeaks.py
```

---

## 🚀 2. Manual Installation Steps

Agar aap ek-ek command chala kar setup karna chahte hain:

```bash
# 1. Purana repository clear karein
cd ~ && rm -rf FeaturesticLeaks-Toolkit-

# 2. Termux packages install karein
pkg update -y && pkg install -y git python clang libffi zlib make nano

# 3. Required Python modules install karein
pip install rich requests pycryptodome zstandard

# 4. Repository clone karein
git clone https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git

# 5. Project folder me jayein
cd FeaturesticLeaks-Toolkit-

# 6. Main Python tool run karein
python FeaturesticLeaks.py
```

---

## 🛠️ 3. Detailed Main Menu Guide

Jab aap `python FeaturesticLeaks.py` run karenge, screen par main menu dikhega:

---

### 📦 Option 1: UNPACK ALL TYPES PAKS
* **Use Case**: Target `.pak` ya `.obb` file ke andar ke saare game assets (textures, Lua scripts, configs) extract karne ke liye.
* **Step-by-Step Instructions**:
  1. Apni `.pak` file ko Termux me `PAK/` folder ke andar copy karein:
     ```bash
     cp /sdcard/Download/game.pak PAK/
     ```
  2. Tool me `1` press karke Enter dabayein.
  3. Screen par dikhne wali `.pak` files me se apni file ka number select karein.
  4. Script file ko unpack karke files `UNPACK/<file_name>/` folder me save kar degi.
  5. Ek `Debug_<file_name>.log` file bhi `UNPACK/` me create hoti hai jo detailed header information deti hai.

---

### 🔨 Option 2: REPACK ALL TYPES PAKS
* **Use Case**: Unpack ki hui files ko edit karne ke baad dobara `.pak` container me convert karne ke liye.
* **Step-by-Step Instructions**:
  1. Ensure karein ki aapne pehle Option 1 se `.pak` file unpack kar li hai.
  2. `UNPACK/<file_name>/` ya `REPACK/<file_name>/` me apni modified files place karein.
  3. Main menu me `2` press karein.
  4. Repack mode (`MINI_OBB`, `GAMEPATCH`, ya `OBBZSDIC`) automatically detect hoga.
  5. Repacking complete hone par output `.pak` file `RESULT/` folder me save ho jayegi.

---

### 🔄 Option 3: REPACK ANY SIZE (EXISTING FILES)
* **Use Case**: PAK ke andar pehle se maujood files ko replace karne ke liye, chahe modified file ka size kitna bhi bada ya chota ho.
* **Step-by-Step Instructions**:
  1. Apni original `.pak` file ko `PAK TOOL/PAK/` folder me rakhein:
     ```bash
     cp /sdcard/Download/game.pak "PAK TOOL/PAK/"
     ```
  2. Apni edit ki hui files (same folder structure ke saath) `PAK TOOL/EDIT/` folder me rakhein.
  3. Main menu me `3` press karein.
  4. Tool original `.pak` file ke headers, size offsets, aur index block rebuild karke file ko replace kar dega.
  5. Final output `PAK TOOL/RESULT/` me milegi.

---

### 🚀 Option 4: REPACK TO PATH (NEW FILES)
* **Use Case**: PAK container me kisi specific internal path par brand new files ya folders add karne ke liye.
* **Step-by-Step Instructions**:
  1. Original `.pak` file ko `PAK TOOL/PAK/` me rakhein.
  2. Jo nayi files inject karni hain unhe `PAK TOOL/EDIT/` me rakhein.
  3. Main menu me `4` press karein.
  4. Screen par target internal path poochead jayega. Internal path enter karein (e.g. `Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`).
  5. Tool target path par naye files safely inject karke game-ready `.pak` rebuild kar dega (`PAK TOOL/RESULT/`).
  6. **Game Ready**: Is method se game login stuck ya crash hone ka issue 100% resolve rehta hai.

---

### 🗑️ Option 5: DELETE FOLDER
* **Use Case**: Workspaces clear karne aur Termux storage free karne ke liye.
* **Step-by-Step Instructions**:
  1. Main menu me `5` press karein.
  2. Temporary output folders ki list dikhegi.
  3. Folder number select karke `yes` type karein aur delete confirm karein.

---

## 🚨 Common Termux Questions & Fixes

### Q1: `python: can't open file 'FeaturesticLeaks.py': No such file or directory`
* **Fix**: Check karein ki aap `FeaturesticLeaks-Toolkit-` directory ke andar ho:
  ```bash
  cd ~/FeaturesticLeaks-Toolkit- && python FeaturesticLeaks.py
  ```

### Q2: `pip install pip is forbidden on Termux`
* **Fix**: Termux me `pip` ko upgrade mat karein, direct packages install karein:
  ```bash
  pip install rich requests pycryptodome zstandard
  ```

### Q3: Quick Launch Command (`paktool`)
* **Fix**: Pehli baar `run.sh` chalane par `paktool` shortcut binary ban jaati hai. Iske baad aap Termux me direct type karke launch kar sakte hain:
  ```bash
  paktool
  ```
  *Ya direct launcher script se:*
  ```bash
  chmod +x run.sh && ./run.sh
  ```

---

## 👤 Credits
* **Tool Name**: `FeaturesticLeaks PAK Tool v2.0`
* **Telegram Channel**: https://t.me/FeaturesticLeaks
