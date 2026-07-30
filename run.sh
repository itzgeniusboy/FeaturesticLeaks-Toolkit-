#!/usr/bin/env bash
# ==============================================================================
# TERMUX AUTO-LAUNCHER & INSTALLER SCRIPT
# TOOL : FEATURESTIC LEAKS PAK TOOL v2.0
# DEVELOPER TELEGRAM : @L359D (https://t.me/L359D)
# TELEGRAM CHANNEL : https://t.me/FeaturesticLeaks
# ==============================================================================

set -e

echo -e "\e[1;36m[+] FeaturesticLeaks PAK Tool v2.0 - Termux Launcher\e[0m"
echo -e "\e[1;32m👤 Developer Telegram: @L359D (https://t.me/L359D)\e[0m"
echo -e "\e[1;33m📢 Official Telegram Channel: https://t.me/FeaturesticLeaks\e[0m\n"

# Check & Request Storage Permission in Termux
if command -v termux-setup-storage &> /dev/null; then
    if [ ! -d "$HOME/storage" ]; then
        echo -e "\e[1;33m[!] Requesting Storage Permission...\e[0m"
        termux-setup-storage
    fi
fi

# Quick Dependency Check
MISSING_PKGS=()
for pkg in python git clang libffi zlib make nano; do
    if ! command -v $pkg &> /dev/null; then
        MISSING_PKGS+=($pkg)
    fi
done

if [ ${#MISSING_PKGS[@]} -ne 0 ]; then
    echo -e "\e[1;33m[+] Installing required Termux packages: ${MISSING_PKGS[*]}...\e[0m"
    pkg update -y && pkg install -y ${MISSING_PKGS[*]}
fi

# Python library installation check
echo -e "\e[1;36m[+] Verifying Python requirements (rich, requests, pycryptodome, zstandard, pytz, gmalg)...\e[0m"
python3 -c "import rich, requests, Crypto, zstandard, pytz, gmalg" 2>/dev/null || {
    echo -e "\e[1;33m[+] Installing missing Python modules...\e[0m"
    pip install rich requests pycryptodome zstandard pytz gmalg
}

# Ensure workspaces exist
mkdir -p PAK UNPACK REPACK RESULT "PAK TOOL/PAK" "PAK TOOL/EDIT" "PAK TOOL/UNPACK" "PAK TOOL/RESULT"

# Create global shortcut 'paktool' in Termux bin if possible
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR=""

if [ -n "$PREFIX" ] && [ -d "$PREFIX/bin" ]; then
    BIN_DIR="$PREFIX/bin"
elif [ -d "/data/data/com.termux/files/usr/bin" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
elif [ -d "$HOME/.local/bin" ]; then
    BIN_DIR="$HOME/.local/bin"
fi

if [ -n "$BIN_DIR" ]; then
    echo "#!/usr/bin/env bash" > "$BIN_DIR/paktool"
    echo "cd \"$SCRIPT_DIR\" && python3 FeaturesticLeaks.py \"\$@\"" >> "$BIN_DIR/paktool"
    chmod +x "$BIN_DIR/paktool"
    echo -e "\e[1;32m[✔] Quick command created/updated in $BIN_DIR/paktool!\e[0m"
fi

if [ -f "FeaturesticLeaks.py" ]; then
    chmod +x FeaturesticLeaks.py
    echo -e "\e[1;32m[✔] Launching FeaturesticLeaks PAK Tool v2.0...\e[0m\n"
    python3 FeaturesticLeaks.py
else
    echo -e "\e[1;31m[✖] Error: FeaturesticLeaks.py file not found in current directory!\e[0m"
    exit 1
fi

