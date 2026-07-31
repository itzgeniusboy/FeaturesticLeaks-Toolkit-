#!/data/data/com.termux/files/usr/bin/sh
echo "=========================================="
echo "⚡ FeaturesticLeaks Termux Auto-Setup ⚡"
echo "👤 Developer: @L359D (Telegram)"
echo "📢 Channel: https://t.me/FeaturesticLeaks"
echo "=========================================="

echo "[1/4] Setting up storage permissions..."
if command -v termux-setup-storage > /dev/null 2>&1; then
    termux-setup-storage
fi

echo "[2/4] Updating package manager & installing tools (python, lua51, luajit, zstd)..."
pkg update -y && pkg install -y python python-pip lua51 luajit zstd git clang libffi zlib make nano unzip

echo "[3/4] Installing Python requirements..."
pip install rich requests pytz gmalg pycryptodome zstandard

echo "[4/4] Creating SDCard & workspace folders..."
mkdir -p /sdcard/FeaturesticLeaks/PAK
mkdir -p /sdcard/FeaturesticLeaks/REPLACE
mkdir -p /sdcard/FeaturesticLeaks/INJECT
mkdir -p /sdcard/FeaturesticLeaks/UNPACK
mkdir -p /sdcard/FeaturesticLeaks/RESULT
mkdir -p /sdcard/FeaturesticLeaks/LUA
mkdir -p /sdcard/FeaturesticLeaks/DUMP_LOGS

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
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
cd "$SCRIPT_DIR" && python3 "$SCRIPT_PATH" "\$@"
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
