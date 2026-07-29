#!/usr/bin/bash
# ==============================================================================
# TERMUX AUTO-LAUNCHER & INSTALLER SCRIPT
# TOOL : FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE
# ==============================================================================

set -e

echo -e "\e[1;32m[+] Updating Termux Package Repositories...\e[0m"
pkg update -y

echo -e "\e[1;36m[+] Installing Core Runtime Tools (Python, PHP, Git, Clang, OpenSSL)...\e[0m"
pkg install -y python php git clang libffi zlib make nano

echo -e "\e[1;33m[+] Installing Required Python Packages (Rich, Requests, PyCryptodome, Zstandard)...\e[0m"
pip install rich requests pycryptodome zstandard

echo -e "\e[1;32m[+] Creating Default Workspace Folder Architecture...\e[0m"
mkdir -p pak/original pak/results/unpack pak/results/repack
mkdir -p lua/original lua/decompiled lua/compiled
mkdir -p zip/extracted zip/output
mkdir -p injector/backup injector/target

if [ -f "FeaturesticLeaks.py" ]; then
    echo -e "\e[1;36m[+] Setting Executable Permissions on FeaturesticLeaks.py...\e[0m"
    chmod +x FeaturesticLeaks.py
    echo -e "\e[1;32m[✔] Launching FeaturesticLeaks PAK Tool...\e[0m\n"
    python3 FeaturesticLeaks.py
else
    echo -e "\e[1;31m[✖] FeaturesticLeaks.py file missing! Running FeaturesticLeaks.py directly...\e[0m"
fi
