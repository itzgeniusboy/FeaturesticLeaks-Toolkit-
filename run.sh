#!/usr/bin/env bash
# ==============================================================================
# TOOL         : FEATURESTIC LEAKS PAK TOOL v2.0
# GUI LAYER    : Termux-API Dialogs & File Picker Wrapper
# DEVELOPER    : @L359D (https://t.me/L359D)
# CHANNEL      : https://t.me/FeaturesticLeaks
# ==============================================================================
# This script adds a native Termux-API GUI interface over FeaturesticLeaks.py.
# Supports --cli flag or automatic fallback if termux-api is not installed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/FeaturesticLeaks.py"
CLI_MODE=0

# ==================== CLI / ARGUMENT PARSING ====================
# Check for --cli flag to force standard text menu
for arg in "$@"; do
    if [ "$arg" = "--cli" ] || [ "$arg" = "-c" ]; then
        CLI_MODE=1
    fi
done

# ==================== SECTION 1: STARTUP CHECK ====================
# Checks if termux-api package & Termux:API app binaries are installed
check_termux_api() {
    if ! command -v termux-toast &> /dev/null || ! command -v termux-dialog &> /dev/null; then
        echo -e "\e[1;31m[✖] Termux:API tools not found!\e[0m"
        echo -e "\e[1;33m👉 Please install Termux:API app from Play Store / F-Droid\e[0m"
        echo -e "\e[1;33m👉 Also install termux-api package: pkg install termux-api jq\e[0m\n"
        echo -e "\e[1;36m[!] Falling back to standard CLI Text Menu...\e[0m"
        sleep 2
        return 1
    fi
    return 0
}

# Ensure workspaces exist
mkdir -p /sdcard/FeaturesticLeaks/PAK \
         /sdcard/FeaturesticLeaks/UNPACK \
         /sdcard/FeaturesticLeaks/REPACK \
         /sdcard/FeaturesticLeaks/RESULT \
         /sdcard/FeaturesticLeaks/LUA

# If CLI_MODE forced or termux-api missing, run standard Python CLI interface
if [ "$CLI_MODE" -eq 1 ] || ! check_termux_api; then
    echo -e "\e[1;32m[+] Launching FeaturesticLeaks in CLI Mode...\e[0m"
    exec python3 "$PYTHON_SCRIPT" "$@"
fi

# ==================== HELPER FUNCTIONS FOR TERMUX GUI ====================

# Helper function to parse JSON output from termux-dialog using jq (or Python fallback)
parse_json_field() {
    local json_str="$1"
    local field="$2"
    if command -v jq &> /dev/null; then
        echo "$json_str" | jq -r ".${field} // empty"
    else
        python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('$field', ''))" <<< "$json_str"
    fi
}

# ==================== SECTION 3: FILE PICKER WRAPPER ====================
# Flexible File Picker supporting termux-storage-get or custom folder listing
pick_file_gui() {
    local prompt_title="$1"
    local filter_ext="$2"  # e.g., ".lua", ".luac", ".pak", or ""
    local base_dir="${3:-/sdcard/FeaturesticLeaks}"

    # Dialog to ask user for picking method
    local method_json
    method_json=$(termux-dialog radio -t "$prompt_title - Choose Method" -v "Android Storage Picker (termux-storage-get),Browse Folder ($base_dir),Cancel")
    
    local method_code
    method_code=$(parse_json_field "$method_json" "code")
    local method_idx
    method_idx=$(parse_json_field "$method_json" "index")

    if [ "$method_code" -ne 0 ] || [ "$method_idx" -eq 2 ]; then
        echo ""
        return 1
    fi

    local selected_file=""

    if [ "$method_idx" -eq 0 ]; then
        # Method 1: Android Native File Picker via termux-storage-get
        termux-toast -s "Opening File Picker..."
        local tmp_file
        tmp_file=$(mktemp)
        if termux-storage-get "$tmp_file"; then
            selected_file="$tmp_file"
        fi
    else
        # Method 2: Custom folder-listing wrapper using ls + termux-dialog radio
        if [ ! -d "$base_dir" ]; then
            mkdir -p "$base_dir"
        fi

        # Find matching files in directory
        local files=()
        while IFS= read -r f; do
            [ -n "$f" ] && files+=("$f")
        done < <(find "$base_dir" -maxdepth 3 -type f \( -name "*$filter_ext" \) 2>/dev/null | head -n 30)

        if [ ${#files[@]} -eq 0 ]; then
            termux-dialog confirm -t "No Files Found" -m "No files matching '$filter_ext' found in $base_dir" > /dev/null
            return 1
        fi

        # Build comma-separated display list
        local file_list_str=""
        for file_path in "${files[@]}"; do
            local rel_name="${file_path#$base_dir/}"
            if [ -z "$file_list_str" ]; then
                file_list_str="$rel_name"
            else
                file_list_str="$file_list_str,$rel_name"
            fi
        done

        local pick_json
        pick_json=$(termux-dialog radio -t "$prompt_title - Select File" -v "$file_list_str")
        local pick_code
        pick_code=$(parse_json_field "$pick_json" "code")
        local pick_idx
        pick_idx=$(parse_json_field "$pick_json" "index")

        if [ "$pick_code" -eq 0 ] && [ "$pick_idx" -ge 0 ] 2>/dev/null; then
            selected_file="${files[$pick_idx]}"
        fi
    fi

    if [ -n "$selected_file" ] && [ -f "$selected_file" ]; then
        echo "$selected_file"
        return 0
    else
        return 1
    fi
}

# ==================== SECTION 6: CORE FUNCTION IMPLEMENTATIONS ====================

# 1. Unpack Function
unpack() {
    local target_file="$1"
    [ -z "$target_file" ] && target_file=$(pick_file_gui "Unpack PAK/OBB" ".pak" "/sdcard/FeaturesticLeaks/PAK")
    
    if [ -n "$target_file" ] && [ -f "$target_file" ]; then
        termux-toast "Processing Unpack: $(basename "$target_file")..."
        if python3 -c "import sys, pathlib; from FeaturesticLeaks import TencentPakFile, dump_unpacking_log; p=pathlib.Path(sys.argv[1]); pak=TencentPakFile(p); out=pathlib.Path('/sdcard/FeaturesticLeaks/UNPACK')/p.stem; pak.dump(out); dump_unpacking_log(pak, out/f'Debug_{p.stem}.log')" "$target_file"; then
            termux-toast "✅ Done: Unpacked $(basename "$target_file")"
        else
            termux-dialog confirm -t "Unpack Error" -m "Failed to unpack $target_file" > /dev/null
        fi
    fi
}

# 2. Repack Function
repack() {
    local target_file="$1"
    [ -z "$target_file" ] && target_file=$(pick_file_gui "Repack PAK/OBB" ".pak" "/sdcard/FeaturesticLeaks/PAK")

    if [ -n "$target_file" ] && [ -f "$target_file" ]; then
        termux-toast "Processing Repack: $(basename "$target_file")..."
        if python3 -c "import sys, pathlib; from FeaturesticLeaks import TencentPakFile, detect_repack_mode, repack_mini_obb, repack_gamepatch, repack_obbzsdic; p=pathlib.Path(sys.argv[1]); pak=TencentPakFile(p); rdir=pathlib.Path('/sdcard/FeaturesticLeaks/REPACK')/p.stem; out=pathlib.Path('/sdcard/FeaturesticLeaks/RESULT')/p.name; mode=detect_repack_mode(p); repack_mini_obb(pak, rdir, out) if mode=='MINI_OBB' else (repack_gamepatch(pak, rdir, out) if mode=='GAMEPATCH' else repack_obbzsdic(pak, rdir, out))" "$target_file"; then
            termux-toast "✅ Done: Repacked $(basename "$target_file")"
        else
            termux-dialog confirm -t "Repack Error" -m "Failed to repack $target_file" > /dev/null
        fi
    fi
}

# 3. Update Offsets Function
update_offsets() {
    termux-toast "Processing: Auto Updating Offsets..."
    if python3 -c "import pathlib; from FeaturesticLeaks import check_and_auto_update; check_and_auto_update()"; then
        termux-toast "✅ Done: Auto Offsets Updated"
    else
        termux-dialog confirm -t "Update Error" -m "Failed to auto update offsets" > /dev/null
    fi
}

# 4. Lua Compiler Function (.lua -> bytecode)
run_lua_compiler() {
    local lua_file="$1"
    [ -z "$lua_file" ] && lua_file=$(pick_file_gui "Compile Lua" ".lua" "/sdcard/FeaturesticLeaks/LUA")

    if [ -n "$lua_file" ] && [ -f "$lua_file" ]; then
        termux-toast "Processing: Compiling $(basename "$lua_file")..."
        if python3 -c "import sys, pathlib; from FeaturesticLeaks import run_lua_compiler; run_lua_compiler(pathlib.Path('/sdcard/FeaturesticLeaks'))" "$lua_file"; then
            termux-toast "✅ Done: Compiled $(basename "$lua_file")"
        else
            termux-dialog confirm -t "Lua Compile Error" -m "Failed to compile $lua_file" > /dev/null
        fi
    fi
}

# 5. Lua Decompiler Function (.luac/bytecode -> .lua)
run_lua_decompiler() {
    local luac_file="$1"
    [ -z "$luac_file" ] && luac_file=$(pick_file_gui "Decompile Lua" ".luac" "/sdcard/FeaturesticLeaks/LUA")

    if [ -n "$luac_file" ] && [ -f "$luac_file" ]; then
        termux-toast "Processing: Decompiling $(basename "$luac_file")..."
        if python3 -c "import sys, pathlib; from FeaturesticLeaks import run_lua_decompiler; run_lua_decompiler(pathlib.Path('/sdcard/FeaturesticLeaks'))" "$luac_file"; then
            termux-toast "✅ Done: Decompiled $(basename "$luac_file")"
        else
            termux-dialog confirm -t "Lua Decompile Error" -m "Failed to decompile $luac_file" > /dev/null
        fi
    fi
}

# ==================== SECTION 2 & 5: MAIN MENU & LOOP ====================
# GUI Main Menu loop using termux-dialog radio
gui_main_menu() {
    while true; do
        local menu_json
        menu_json=$(termux-dialog radio \
            -t "⚡ FEATURESTIC LEAKS PAK TOOL v2.0" \
            -v "Unpack File,Pack / Repack File,Auto Update Offsets,Lua Compile,Lua Decompile,Exit")

        local code
        code=$(parse_json_field "$menu_json" "code")
        local idx
        idx=$(parse_json_field "$menu_json" "index")

        # If user closed dialog or pressed Cancel
        if [ "$code" -ne 0 ] || [ "$idx" -eq -1 ] 2>/dev/null; then
            termux-toast "Exiting Featurestic Leaks GUI..."
            break
        fi

        case "$idx" in
            0)
                # Unpack File
                unpack
                ;;
            1)
                # Pack / Repack File
                repack
                ;;
            2)
                # Auto Update Offsets
                update_offsets
                ;;
            3)
                # Lua Compile
                run_lua_compiler
                ;;
            4)
                # Lua Decompile
                run_lua_decompiler
                ;;
            5)
                # Exit
                termux-toast "Goodbye!"
                break
                ;;
            *)
                termux-toast "Invalid Selection"
                ;;
        esac
    done
}

# Launch GUI Menu
gui_main_menu
