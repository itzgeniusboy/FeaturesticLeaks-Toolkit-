#!/data/data/com.termux/files/usr/bin/sh
echo "=========================================="
echo "⚡ FeaturesticLeaks Termux Auto-Setup ⚡"
echo "👤 Developer: @L359D (Telegram)"
echo "📢 Channel: https://t.me/FeaturesticLeaks"
echo "=========================================="

echo "[1/4] Setting up storage permissions..."
termux-setup-storage

echo "[2/4] Updating package manager..."
pkg update -y && pkg install -y python python-pip

echo "[3/4] Installing Python requirements..."
pip install rich requests pytz gmalg pycryptodome zstandard

echo "[4/4] Creating SDCard workspace folders..."
mkdir -p /sdcard/FeaturesticLeaks/PAK
mkdir -p /sdcard/FeaturesticLeaks/REPLACE
mkdir -p /sdcard/FeaturesticLeaks/INJECT
mkdir -p /sdcard/FeaturesticLeaks/UNPACK
mkdir -p /sdcard/FeaturesticLeaks/RESULT

SCRIPT_PATH="$(pwd)/FeaturesticLeaks.py"
LEAK_CMD="/data/data/com.termux/files/usr/bin/leak"

if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    echo "#!/data/data/com.termux/files/usr/bin/sh" > "$LEAK_CMD"
    echo "python3 \"$SCRIPT_PATH\" \"\$@\"" >> "$LEAK_CMD"
    chmod +x "$LEAK_CMD"
    echo "[OK] 'leak' command shortcut installed!"
fi

echo "=========================================="
echo "🎉 Setup Completed Successfully!"
echo "Ab aap Termux me kisi bhi jagah sirf 'leak' type karke tool launch kar sakte ho!"
echo "=========================================="
