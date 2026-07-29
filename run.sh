#!/usr/bin/env bash
# ==============================================================================
# TERMUX AUTO-LAUNCHER & INSTALLER SCRIPT
# TOOL : FEATURESTIC LEAKS PAK TOOL v2.0
# TELEGRAM CHANNEL : https://t.me/FeaturesticLeaks
# ==============================================================================

set -e

echo -e "\e[1;36m[+] FeaturesticLeaks PAK Tool v2.0 - Termux Launcher\e[0m"
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
echo -e "\e[1;36m[+] Verifying Python requirements (rich, requests, pycryptodome, zstandard)...\e[0m"
python3 -c "import rich, requests, Crypto, zstandard" 2>/dev/null || {
    echo -e "\e[1;33m[+] Installing missing Python modules...\e[0m"
    pip install rich requests pycryptodome zstandard
}

# Ensure workspaces exist
mkdir -p PAK UNPACK REPACK RESULT "PAK TOOL/PAK" "PAK TOOL/EDIT" "PAK TOOL/UNPACK" "PAK TOOL/RESULT"

# Create global shortcut 'paktool' in Termux bin if possible
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$PREFIX/bin" ] && [ ! -f "$PREFIX/bin/paktool" ]; then
    echo -e "\e[1;36m[+] Creating Termux quick command 'paktool'...\e[0m"
    echo "#!/usr/bin/env bash" > "$PREFIX/bin/paktool"
    echo "cd \"$SCRIPT_DIR\" && ./run.sh" >> "$PREFIX/bin/paktool"
    chmod +x "$PREFIX/bin/paktool"
    echo -e "\e[1;32m[✔] Quick command created! You can now launch this tool by typing 'paktool' anywhere in Termux.\e[0m"
fi

if [ -f "FeaturesticLeaks.py" ]; then
    chmod +x FeaturesticLeaks.py
    echo -e "\e[1;32m[✔] Launching FeaturesticLeaks PAK Tool v2.0...\e[0m\n"
    python3 FeaturesticLeaks.py
else
    echo -e "\e[1;31m[✖] Error: FeaturesticLeaks.py file not found in current directory!\e[0m"
    exit 1
fi

