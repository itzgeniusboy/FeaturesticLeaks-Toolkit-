#!/data/data/com.termux/files/usr/bin/sh
# ==============================================================================
# TOOL         : FEATURESTIC LEAKS PAK TOOL v2.7
# SETUP SCRIPT : Minimal CLI Sparse-Checkout & Environment Installer
# DEVELOPER    : @L359D (Telegram)
# CHANNEL      : https://t.me/FeaturesticLeaks
# ==============================================================================

echo "=========================================="
echo "⚡ FeaturesticLeaks Termux Auto-Setup ⚡"
echo "👤 Developer: @L359D (Telegram)"
echo "📢 Channel: https://t.me/FeaturesticLeaks"
echo "=========================================="

REPO_URL="https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-.git"
TARGET_DIR="FeaturesticLeaks-Toolkit-"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# If setup.sh is run outside the repo folder, clone via sparse-checkout
if [ ! -f "$SCRIPT_DIR/FeaturesticLeaks.py" ] && [ ! -d "$SCRIPT_DIR/pak" ]; then
    echo "[*] Performing minimal Sparse-Checkout clone (CLI files only)..."
    git clone --filter=blob:none --no-checkout "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
    git sparse-checkout init --cone
    git sparse-checkout set \
      FeaturesticLeaks.py \
      run.sh \
      setup.sh \
      README.md \
      DOCUMENTATION.md \
      .gitignore \
      ai \
      core \
      lua \
      pak
    git checkout main || git checkout master
    SCRIPT_DIR="$(pwd)"
fi

echo "[1/4] Setting up storage permissions..."
if command -v termux-setup-storage > /dev/null 2>&1; then
    termux-setup-storage
fi

echo "[2/4] Updating package manager & installing tools (python, termux-api, jq, lua51, luajit, zstd)..."
if command -v pkg > /dev/null 2>&1; then
    pkg update -y && pkg install -y python python-pip termux-api jq lua51 luajit zstd git clang libffi zlib make nano unzip
fi

echo "[3/4] Installing Python requirements..."
if command -v pip > /dev/null 2>&1; then
    pip install rich requests pytz gmalg pycryptodome zstandard
elif command -v pip3 > /dev/null 2>&1; then
    pip3 install rich requests pytz gmalg pycryptodome zstandard
fi

# Configure sparse-checkout if inside git repo so future pulls only fetch CLI files
if [ -d "$SCRIPT_DIR/.git" ]; then
    echo "[*] Configuring Git sparse-checkout for minimal CLI footprint..."
    (
        cd "$SCRIPT_DIR"
        git sparse-checkout init --cone 2>/dev/null || true
        git sparse-checkout set \
          FeaturesticLeaks.py \
          run.sh \
          setup.sh \
          README.md \
          DOCUMENTATION.md \
          .gitignore \
          ai \
          core \
          lua \
          pak 2>/dev/null || true
    )
fi

echo "[Clean] Removing unnecessary Web / UI / Scaffold files from local workspace..."
for f in server.js package.json metadata.json index.html vite.config.ts tsconfig.json bun.lock; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        rm -f "$SCRIPT_DIR/$f" 2>/dev/null && echo "Removed unnecessary file: $f"
    fi
done
if [ -d "$SCRIPT_DIR/src" ]; then
    rm -rf "$SCRIPT_DIR/src" 2>/dev/null && echo "Removed unnecessary folder: src/"
fi
echo "✅ Sirf zaroori Termux files download hui — UI/web dashboard files skip kar di gayi."

echo "[4/4] Creating SDCard & workspace folders..."
mkdir -p /sdcard/FeaturesticLeaks/PAK 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/REPLACE 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/INJECT 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/UNPACK 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/RESULT 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/LUA 2>/dev/null || true
mkdir -p /sdcard/FeaturesticLeaks/DUMP_LOGS 2>/dev/null || true

SCRIPT_PATH="$SCRIPT_DIR/FeaturesticLeaks.py"

BIN_DIR=""
if [ -n "$PREFIX" ] && [ -d "$PREFIX/bin" ]; then
    BIN_DIR="$PREFIX/bin"
elif [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
fi

if [ -n "$BIN_DIR" ]; then
    for CMD in leak paktool; do
        cat <<EOF > "$BIN_DIR/$CMD"
#!/data/data/com.termux/files/usr/bin/sh
cd "$SCRIPT_DIR" && bash "$SCRIPT_DIR/run.sh" "\$@"
EOF
        chmod +x "$BIN_DIR/$CMD"
    done
    echo "[OK] 'leak' and 'paktool' command shortcuts installed in $BIN_DIR!"
fi

# Add bashrc/zshrc aliases as backup
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ] || [ "$RC" = "$HOME/.bashrc" ]; then
        grep -q "alias leak=" "$RC" 2>/dev/null || echo "alias leak='cd \"$SCRIPT_DIR\" && python3 \"$SCRIPT_PATH\"'" >> "$RC"
        grep -q "alias paktool=" "$RC" 2>/dev/null || echo "alias paktool='cd \"$SCRIPT_DIR\" && python3 \"$SCRIPT_PATH\"'" >> "$RC"
    fi
done

echo "=========================================="
echo "🎉 Setup Completed Successfully!"
echo "Ab aap Termux me kisi bhi jagah sirf 'leak' ya 'paktool' type karke tool launch kar sakte ho!"
echo "=========================================="
