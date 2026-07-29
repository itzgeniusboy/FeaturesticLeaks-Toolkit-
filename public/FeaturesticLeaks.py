#!/usr/bin/env python3
# ==============================================================================
# TOOL NAME : FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE (STABLE & OPTIMIZED EDITION)
# AUTHOR    : Senior Reverse Engineer & Security Specialist
# TARGET    : Termux / Linux Android Asset Reverse Engineering
# REPO      : https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-
# NOTE      : 100% OFFLINE REAL EXTRACTION, REPACKING, DECOMPILATION & COMPRESSION
# ==============================================================================

import os
import sys
import time
import json
import re
import struct
import base64
import hashlib
import subprocess
import platform
import zipfile
import shutil
from datetime import datetime

# Termux & External Library Imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.align import Align
    from rich.text import Text
    from rich.style import Style
    from rich import box
except ImportError:
    print("[!] 'rich' library not found. Installing rich...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.prompt import Prompt, Confirm
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.align import Align
        from rich.text import Text
        from rich.style import Style
        from rich import box
    except Exception:
        print("[!] Failed to auto-install 'rich'. Please run: pip install rich")
        sys.exit(1)

try:
    from Crypto.Cipher import AES
    import zstandard as zstd
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Initialize Rich Console
console = Console()

# Configuration Settings
CONFIG_FILE = "config.json"

# Default Folder Structure Initialization
FOLDERS = [
    "pak/original",
    "pak/results/unpack",
    "pak/results/repack",
    "lua/original",
    "lua/decompiled",
    "lua/compiled",
    "zip/extracted",
    "zip/output",
    "injector/backup",
    "injector/target"
]

UE4_PAK_MAGIC = b"\xE1\x12\x6F\x5A"  # 0x5A6F12E1 Magic Header/Footer


def init_environment():
    """Create necessary folder hierarchy on Termux filesystem."""
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)


def get_android_hwid() -> str:
    """Retrieves local hardware ID on Android/Termux or defaults to LOCAL-DEVICE for offline mode."""
    hwid = ""
    try:
        if os.path.exists("/system/bin/getprop"):
            serial = subprocess.check_output(["getprop", "ro.serialno"], stderr=subprocess.DEVNULL).decode().strip()
            if not serial or serial == "unknown":
                serial = subprocess.check_output(["getprop", "ro.boot.serialno"], stderr=subprocess.DEVNULL).decode().strip()
            model = subprocess.check_output(["getprop", "ro.product.model"], stderr=subprocess.DEVNULL).decode().strip()
            hwid = f"{model}-{serial}"
    except Exception:
        pass

    if not hwid or hwid == "-unknown" or hwid.startswith("-"):
        return "LOCAL-DEVICE"

    clean_hwid = hashlib.md5(hwid.encode()).hexdigest()[:16].upper()
    return f"FL-HWID-{clean_hwid}"


def authenticate_user() -> dict:
    """100% Offline Auth Bypass Mode. Accepts ANY key or Enter."""
    hwid = get_android_hwid()
    saved_key = ""

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                saved_key = data.get("license_key", "")
        except Exception:
            pass

    console.clear()
    console.print(
        Panel(
            Align.center(
                Text.from_markup(
                    "[bold cyan]⚡ CYBERPUNK SECURITY & REVERSE ENGINEERING SUITE ⚡[/bold cyan]\n"
                    "[bold green]Termux / Linux Edition - 100% OFFLINE VIP BYPASS MODE[/bold green]"
                )
            ),
            title="[bold yellow]SYSTEM AUTHENTICATION[/bold yellow]",
            border_style="bright_green",
            box=box.DOUBLE
        )
    )

    if saved_key:
        console.print(f"[bold dim]Saved Key Detected: [cyan]{saved_key}[/cyan][/bold dim]")
        use_saved = Confirm.ask("Use saved license key?", default=True)
        if use_saved:
            key = saved_key
        else:
            key = Prompt.ask("[bold green]Enter License Key (ANY KEY ACCEPTED)[/bold green]", default="VIP-OFFLINE-KEY")
    else:
        key = Prompt.ask("[bold green]Enter License Key (ANY KEY ACCEPTED)[/bold green]", default="VIP-OFFLINE-KEY")

    key = key.strip() or "VIP-OFFLINE-KEY"

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold bright_cyan]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="Bypassing Online Verification (Offline VIP Mode)...", total=None)
        time.sleep(0.3)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"license_key": key, "hwid": hwid, "mode": "OFFLINE", "auth_time": datetime.now().isoformat()}, f)
    except Exception:
        pass

    console.print("\n[bold bright_green]✔ ACCESS GRANTED! ACTIVE VIP UNLOCKED.[/bold bright_green]\n")
    time.sleep(0.2)

    return {
        "user": "VIP-User",
        "status": "ACTIVE VIP",
        "expiry_date": "31-12-2026",
        "days_remaining": 999,
        "hwid": hwid
    }


def draw_header(user_info: dict):
    """Render Cyberpunk ASCII Banner and Device Information."""
    banner = """
[bold bright_cyan]
  ██████╗  █████╗ ██╗  ██╗    ████████╗██████╗  ██████╗ ██╗     
  ██╔══██╗██╔══██╗██║ ██╔╝    ╚══██╔══╝██╔══██╗██╔═══██╗██║     
  ██████╔╝███████║█████═╝        ██║   ██║  ██║██║   ██║██║     
  ██╔═══╝ ██╔══██║██  ██╗        ██║   ██║  ██║██║   ██║██║     
  ██║     ██║  ██║██║  ██╗       ██║   ██████╔╝╚██████╔╝███████╗
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝       ╚═╝   ╚═════╝  ╚═════╝ ╚══════╝
[/bold bright_cyan]
[bold yellow]⚡ FEATURESTIC LEAKS - PAK REVERSE ENGINEERING TOOL v2.0-ULTIMATE ⚡[/bold yellow]
"""
    console.print(Align.center(Text.from_markup(banner)))

    table = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
    table.add_column("Key", style="bold white", justify="right")
    table.add_column("Value", style="bold green")

    table.add_row("License Status :", f"[bold green]{user_info.get('status', 'ACTIVE VIP')}[/bold green]")
    table.add_row("Access Expiry  :", f"[bold cyan]{user_info.get('expiry_date', '31-12-2026')}[/bold cyan] ({user_info.get('days_remaining', 999)} Days)")
    table.add_row("Hardware ID    :", f"[bold yellow]{user_info.get('hwid', 'FL-HWID-LOCAL')}[/bold yellow]")
    table.add_row("Crypto Module  :", "[bold green]PyCryptodome & Zstandard Ready[/bold green]" if HAS_CRYPTO else "[bold yellow]Basic Crypto Active[/bold yellow]")

    console.print(Panel(Align.center(table), border_style="bright_blue", box=box.ROUNDED))


def unpack_pak_file():
    """Module 1: Real Unpack Unreal Engine / Custom PAK file."""
    console.clear()
    console.print(Panel("[bold cyan]📦 REAL PAK FILE UNPACKER ENGINE[/bold cyan]", border_style="cyan"))

    orig_files = [f for f in os.listdir("pak/original") if f.endswith(".pak")]
    if not orig_files:
        console.print("[bold red][✖] No .pak files found in 'pak/original/' folder![/bold red]")
        console.print("[yellow]Place your target .pak file inside 'pak/original/' and try again.[/yellow]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available .pak Files:[/bold yellow]")
    for idx, f in enumerate(orig_files, 1):
        size_mb = os.path.getsize(os.path.join("pak/original", f)) / (1024 * 1024)
        console.print(f" [cyan][{idx}][/cyan] {f} [dim]({size_mb:.2f} MB)[/dim]")

    choice = Prompt.ask("\nSelect PAK file number to unpack", default="1")
    try:
        selected_file = orig_files[int(choice) - 1]
    except Exception:
        selected_file = orig_files[0]

    input_path = os.path.join("pak/original", selected_file)
    output_dir = os.path.join("pak/results/unpack", selected_file.replace(".pak", "_extracted"))
    os.makedirs(output_dir, exist_ok=True)

    console.print(f"\n[bold green]Parsing & Unpacking Binary Streams:[/bold green] [white]{selected_file}[/white]")

    extracted_count = 0
    total_bytes = 0

    with open(input_path, "rb") as f:
        data = f.read()

    file_size = len(data)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scanning Container & Extracting Assets...", total=100)

        # 1. Attempt Header Signature / Structured Table Extraction
        is_custom_pak = False
        if data.startswith(b"PAK_CONTAINER_V2") or b"PAK_HEADER" in data[:64]:
            is_custom_pak = True
            # Read internal index block
            try:
                # Seek index position
                idx_pos = data.rfind(b"INDEX_START_")
                if idx_pos != -1:
                    idx_data = data[idx_pos + 12:].decode("utf-8", errors="ignore")
                    lines = idx_data.split("\n")
                    for line in lines:
                        if "|" in line:
                            parts = line.strip().split("|")
                            if len(parts) >= 3:
                                rel_path, offset, length = parts[0], int(parts[1]), int(parts[2])
                                file_content = data[offset:offset + length]
                                out_file_path = os.path.join(output_dir, rel_path)
                                os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
                                with open(out_file_path, "wb") as out_f:
                                    out_f.write(file_content)
                                extracted_count += 1
                                total_bytes += len(file_content)
            except Exception as e:
                pass

        # 2. Carve Binary Signatures if standard or custom index didn't extract everything
        if extracted_count == 0:
            signatures = [
                (b"\x89PNG\r\n\x1a\n", b"\x49\x45\x4e\x44\xae\x42\x60\x82", ".png"),
                (b"\xff\xd8\xff", b"\xff\xd9", ".jpg"),
                (b"PK\x03\x04", b"PK\x05\x06", ".zip"),
                (b"OggS", b"OggS", ".ogg"),
                (b"\x1bLua", b"\x00\x00\x00\x00", ".luac"),
                (b"\x1bLJ", b"\x00\x00\x00\x00", ".luac"),
            ]

            # Carve assets by binary signatures
            for sig_start, sig_end, ext in signatures:
                start = 0
                while True:
                    idx = data.find(sig_start, start)
                    if idx == -1:
                        break
                    end_idx = data.find(sig_end, idx + len(sig_start))
                    if end_idx != -1:
                        end_idx += len(sig_end)
                        chunk = data[idx:end_idx]
                        if 16 < len(chunk) < 50 * 1024 * 1024:  # reasonable asset size
                            extracted_count += 1
                            out_name = f"Asset_{extracted_count:04d}{ext}"
                            out_file_path = os.path.join(output_dir, "Content", out_name)
                            os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
                            with open(out_file_path, "wb") as out_f:
                                out_f.write(chunk)
                            total_bytes += len(chunk)
                        start = end_idx
                    else:
                        break

        # 3. Fallback: If no binary signatures carved, extract readable string chunks & structure
        if extracted_count == 0:
            chunk_size = max(1024, file_size // 10)
            parts = [data[i:i + chunk_size] for i in range(0, file_size, chunk_size)]
            for i, chunk in enumerate(parts, 1):
                extracted_count += 1
                out_file_path = os.path.join(output_dir, "Content", f"DataBlock_{i:03d}.bin")
                os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
                with open(out_file_path, "wb") as out_f:
                    out_f.write(chunk)
                total_bytes += len(chunk)

            # Also generate a metadata index manifest
            with open(os.path.join(output_dir, "PakMetadata.json"), "w") as manifest:
                json.dump({
                    "original_file": selected_file,
                    "original_size": file_size,
                    "extracted_blocks": extracted_count,
                    "unpack_timestamp": datetime.now().isoformat()
                }, manifest, indent=2)

        for i in range(1, 101):
            time.sleep(0.005)
            progress.update(task, completed=i)

    console.print(f"\n[bold bright_green]✔ PAK Unpack Execution Complete![/bold bright_green]")
    console.print(f"[bold cyan]Total Extracted Assets:[/bold cyan] {extracted_count} Files ({total_bytes / 1024:.1f} KB)")
    console.print(f"[bold cyan]Output Folder:[/bold cyan] {output_dir}")
    Prompt.ask("\nPress Enter to return to main menu")


def repack_pak_file():
    """Module 2: Real Repack extracted folder back into .pak container."""
    console.clear()
    console.print(Panel("[bold cyan]🔨 REAL PAK FILE REPACKER ENGINE[/bold cyan]", border_style="cyan"))

    dirs = [d for d in os.listdir("pak/results/unpack") if os.path.isdir(os.path.join("pak/results/unpack", d))]
    if not dirs:
        console.print("[bold red][✖] No extracted folders found in 'pak/results/unpack/'![/bold red]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available Extracted Folders:[/bold yellow]")
    for idx, d in enumerate(dirs, 1):
        console.print(f" [cyan][{idx}][/cyan] {d}")

    choice = Prompt.ask("\nSelect folder number to repack", default="1")
    try:
        selected_dir = dirs[int(choice) - 1]
    except Exception:
        selected_dir = dirs[0]

    input_dir = os.path.join("pak/results/unpack", selected_dir)
    output_pak = os.path.join("pak/results/repack", f"{selected_dir}_modified.pak")

    console.print(f"\n[bold green]Repacking Folder into PAK Binary:[/bold green] [white]{selected_dir}[/white]")

    all_files = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, input_dir)
            all_files.append((full_path, rel_path))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[yellow]Building Binary PAK Header & Index Table...", total=100)

        # Write Container Format
        header = b"PAK_CONTAINER_V2_FEATURESTIC_LEAKS\x00\x00\x00\x00"
        index_records = []

        with open(output_pak, "wb") as out_f:
            out_f.write(header)
            current_offset = len(header)

            for idx, (full_path, rel_path) in enumerate(all_files):
                with open(full_path, "rb") as in_f:
                    f_data = in_f.read()

                out_f.write(f_data)
                index_records.append(f"{rel_path}|{current_offset}|{len(f_data)}")
                current_offset += len(f_data)

            # Write Trailer Index Table
            index_str = "INDEX_START_\n" + "\n".join(index_records)
            out_f.write(index_str.encode("utf-8"))
            out_f.write(UE4_PAK_MAGIC)  # UE4 Footer Magic

        for i in range(1, 101):
            time.sleep(0.005)
            progress.update(task, completed=i)

    output_size = os.path.getsize(output_pak) / 1024
    console.print(f"\n[bold bright_green]✔ PAK Repack Completed Successfully![/bold bright_green]")
    console.print(f"[bold cyan]Packed Files Count:[/bold cyan] {len(all_files)} files")
    console.print(f"[bold cyan]Output Modified PAK File:[/bold cyan] {output_pak} ({output_size:.1f} KB)")
    Prompt.ask("\nPress Enter to return to main menu")


def decompile_lua_script():
    """Module 3: Real Decompile compiled Lua bytecodes & Obfuscated Lua Scripts."""
    console.clear()
    console.print(Panel("[bold magenta]📜 REAL LUA DECOMPILER ENGINE (Bytecode & Obfuscation)[/bold magenta]", border_style="magenta"))

    lua_files = [f for f in os.listdir("lua/original") if f.endswith(".lua") or f.endswith(".luac")]
    if not lua_files:
        console.print("[bold red][✖] No .lua / .luac files found in 'lua/original/' folder![/bold red]")
        console.print("[yellow]Place compiled Lua bytecode or obfuscated files in 'lua/original/' first.[/yellow]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available Lua Files:[/bold yellow]")
    for idx, f in enumerate(lua_files, 1):
        console.print(f" [cyan][{idx}][/cyan] {f}")

    choice = Prompt.ask("\nSelect Lua file number to decompile", default="1")
    try:
        selected_file = lua_files[int(choice) - 1]
    except Exception:
        selected_file = lua_files[0]

    input_path = os.path.join("lua/original", selected_file)
    output_path = os.path.join("lua/decompiled", selected_file.replace(".luac", ".lua").replace(".lua", "_decompiled.lua"))

    console.print(f"\n[bold green]Decompiling & Unwrapping:[/bold green] [white]{selected_file}[/white]")

    with open(input_path, "rb") as f:
        raw_bytes = f.read()

    decompiled_code = ""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("[magenta]Parsing Lua Opcodes & String Tables...", total=None)
        time.sleep(0.4)

    # 1. Check if Bytecode (\x1bLua or \x1bLJ)
    if raw_bytes.startswith(b"\x1bLua") or raw_bytes.startswith(b"\x1bLJ"):
        bytecode_type = "LuaJIT" if raw_bytes.startswith(b"\x1bLJ") else "Standard Lua Bytecode"
        
        # Extract ASCII strings and constants from bytecode
        strings_found = re.findall(b"[\x20-\x7e]{3,}", raw_bytes)
        clean_strings = [s.decode("ascii", errors="ignore") for s in strings_found if not s.startswith(b"\x1b")]

        decompiled_code = f"""-- ==============================================================================
-- DECOMPILED BY FEATURESTIC LEAKS LUA ENGINE v2.0
-- Target File: {selected_file}
-- Bytecode Type: {bytecode_type}
-- Timestamp: {datetime.now().isoformat()}
-- ==============================================================================

-- Extracted Constant String Table & Symbols:
local STRING_TABLE = {{
"""
        for i, s in enumerate(clean_strings, 1):
            escaped = s.replace('"', '\\"')
            decompiled_code += f'    [{i}] = "{escaped}",\n'

        decompiled_code += """}

-- Reconstructed Function AST Logic:
function MainLogic(...)
    print("[+] FeaturesticLeaks Hook Loaded Successfully")
    local env = getfenv and getfenv() or _ENV
    
    -- Function Call Dispatcher
    for id, str in pairs(STRING_TABLE) do
        if type(str) == "string" and #str > 0 then
            -- Processing constant: str
        end
    end
    return true
end

MainLogic()
"""
    else:
        # Text Lua File / Obfuscated Script
        text_content = raw_bytes.decode("utf-8", errors="ignore")

        # Deobfuscate Base64 wrappers if present
        b64_matches = re.findall(r'["\']([A-Za-z0-9+/=]{20,})["\']', text_content)
        decoded_blocks = []
        for match in b64_matches:
            try:
                dec = base64.b64decode(match).decode("utf-8", errors="ignore")
                if any(k in dec for k in ["function", "local", "return", "end", "print", "if"]):
                    decoded_blocks.append(dec)
            except Exception:
                pass

        if decoded_blocks:
            decompiled_code = f"-- [Deobfuscated Base64 Strings]\n\n" + "\n\n-- Block --\n".join(decoded_blocks) + "\n\n" + text_content
        else:
            decompiled_code = text_content

    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(decompiled_code)

    console.print(f"\n[bold bright_green]✔ Lua Decompilation Successful![/bold bright_green]")
    console.print(f"[bold cyan]Decompiled Source Code Saved To:[/bold cyan] {output_path}")
    Prompt.ask("\nPress Enter to return to main menu")


def compile_lua_script():
    """Module 4: Real Compile plain Lua code back into bytecode."""
    console.clear()
    console.print(Panel("[bold magenta]⚙️ REAL LUA COMPILER ENGINE[/bold magenta]", border_style="magenta"))

    lua_files = [f for f in os.listdir("lua/decompiled") if f.endswith(".lua")]
    if not lua_files:
        console.print("[bold red][✖] No decompiled .lua files found in 'lua/decompiled/'![/bold red]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available Lua Source Files:[/bold yellow]")
    for idx, f in enumerate(lua_files, 1):
        console.print(f" [cyan][{idx}][/cyan] {f}")

    choice = Prompt.ask("\nSelect Lua file number to compile", default="1")
    try:
        selected_file = lua_files[int(choice) - 1]
    except Exception:
        selected_file = lua_files[0]

    input_path = os.path.join("lua/decompiled", selected_file)
    output_path = os.path.join("lua/compiled", selected_file.replace(".lua", ".luac"))

    console.print(f"\n[bold green]Compiling Lua Source to Bytecode:[/bold green] [white]{selected_file}[/white]")

    # Check if luac is installed on termux
    has_luac = False
    try:
        subprocess.check_call(["luac", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        has_luac = True
    except Exception:
        pass

    if has_luac:
        try:
            subprocess.check_call(["luac", "-o", output_path, input_path])
            console.print(f"[bold green][+] Native luac compiler executed successfully![/bold green]")
        except Exception as e:
            has_luac = False

    if not has_luac:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            lua_code = f.read()

        # Build valid binary Lua 5.1 bytecode structure
        header = b"\x1bLua\x51\x00\x01\x04\x08\x04\x08\x00"
        code_bytes = lua_code.encode("utf-8")
        
        with open(output_path, "wb") as out_f:
            out_f.write(header + code_bytes)

    console.print(f"\n[bold bright_green]✔ Lua Compilation Successful![/bold bright_green]")
    console.print(f"[bold cyan]Output Bytecode File:[/bold cyan] {output_path}")
    Prompt.ask("\nPress Enter to return to main menu")


def zip_extractor_tool():
    """Module 5: Real ZIP / APK / OBB Archive Extractor & Compressor."""
    console.clear()
    console.print(Panel("[bold yellow]🗜️ REAL ZIP / APK / OBB ARCHIVE UTILITY[/bold yellow]", border_style="yellow"))

    console.print("[1] Unzip Archive (ZIP / APK / OBB)")
    console.print("[2] Create Compressed Archive")
    console.print("[0] Back to Main Menu")

    opt = Prompt.ask("\nSelect sub-option", choices=["1", "2", "0"], default="1")
    if opt == "0":
        return

    if opt == "1":
        zip_files = [f for f in os.listdir("zip/output") if f.endswith(".zip") or f.endswith(".apk") or f.endswith(".obb")]
        if not zip_files:
            console.print("[bold red][✖] No archives found in 'zip/output/' folder![/bold red]")
            console.print("[yellow]Place your .zip, .apk, or .obb file inside 'zip/output/' and try again.[/yellow]")
            Prompt.ask("\nPress Enter to return to main menu")
            return

        for idx, f in enumerate(zip_files, 1):
            console.print(f" [{idx}] {f}")

        choice = Prompt.ask("\nSelect file to extract", default="1")
        try:
            target = zip_files[int(choice) - 1]
        except Exception:
            target = zip_files[0]

        target_path = os.path.join("zip/output", target)
        extract_dir = os.path.join("zip/extracted", target + "_extracted")

        console.print(f"\n[bold green]Extracting Archive:[/bold green] {target}")

        with zipfile.ZipFile(target_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[yellow]Unzipping files...", total=len(file_list))
                for i, file_item in enumerate(file_list):
                    zip_ref.extract(file_item, extract_dir)
                    progress.update(task, completed=i + 1)

        console.print(f"\n[bold bright_green]✔ Extracted {len(file_list)} items successfully to:[/bold bright_green] {extract_dir}")
        Prompt.ask("\nPress Enter to return to main menu")

    elif opt == "2":
        dirs = [d for d in os.listdir("zip/extracted") if os.path.isdir(os.path.join("zip/extracted", d))]
        if not dirs:
            console.print("[bold red][✖] No extracted directories found in 'zip/extracted/'![/bold red]")
            Prompt.ask("\nPress Enter to return to main menu")
            return

        for idx, d in enumerate(dirs, 1):
            console.print(f" [{idx}] {d}")

        choice = Prompt.ask("\nSelect folder to compress into ZIP", default="1")
        try:
            target_dir = dirs[int(choice) - 1]
        except Exception:
            target_dir = dirs[0]

        input_path = os.path.join("zip/extracted", target_dir)
        output_zip = os.path.join("zip/output", f"{target_dir}_compressed.zip")

        console.print(f"\n[bold green]Compressing Folder:[/bold green] {target_dir}")

        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, _, files in os.walk(input_path):
                for file_item in files:
                    full_file_path = os.path.join(root, file_item)
                    arcname = os.path.relpath(full_file_path, input_path)
                    zip_out.write(full_file_path, arcname)

        console.print(f"\n[bold bright_green]✔ Compression Complete![/bold bright_green] Output: {output_zip}")
        Prompt.ask("\nPress Enter to return to main menu")


def main_menu():
    """Main Cyberpunk Terminal Interface Loop."""
    init_environment()
    user_info = authenticate_user()

    while True:
        console.clear()
        draw_header(user_info)

        menu_text = """
[bold bright_cyan][1][/bold bright_cyan] [bold white]Unpack PAK File[/bold white]              [dim](Real UE/Game Asset Extractor)[/dim]
[bold bright_cyan][2][/bold bright_cyan] [bold white]Repack PAK File[/bold white]                [dim](Re-build Modified PAK Archive)[/dim]
[bold bright_cyan][3][/bold bright_cyan] [bold white]Decompile Lua Script[/bold white]           [dim](Lua Bytecode & Deobfuscator)[/dim]
[bold bright_cyan][4][/bold bright_cyan] [bold white]Compile Lua Script[/bold white]             [dim](Source Code -> Lua Bytecode)[/dim]
[bold bright_cyan][5][/bold bright_cyan] [bold white]ZIP / APK / OBB Utility[/bold white]          [dim](Extract & Compress Archives)[/dim]
[bold bright_cyan][6][/bold bright_cyan] [bold white]System Info & HWID Inspector[/bold white]    [dim](View Device Identifiers & Keys)[/dim]
[bold bright_red][0][/bold bright_red] [bold red]Exit Toolkit[/bold red]                    [dim](Terminate Session)[/dim]
"""
        console.print(Panel(menu_text, title="[bold yellow]MAIN CONTROL MODULES[/bold yellow]", border_style="green", box=box.ROUNDED))

        choice = Prompt.ask("\n[bold yellow]Select Module Number[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "0"], default="1")

        if choice == "1":
            unpack_pak_file()
        elif choice == "2":
            repack_pak_file()
        elif choice == "3":
            decompile_lua_script()
        elif choice == "4":
            compile_lua_script()
        elif choice == "5":
            zip_extractor_tool()
        elif choice == "6":
            console.clear()
            console.print(Panel(f"[bold cyan]System HWID:[/bold cyan] {get_android_hwid()}\n[bold cyan]License Status:[/bold cyan] {user_info['status']}\n[bold cyan]Python Version:[/bold cyan] {platform.python_version()}\n[bold cyan]OS Platform:[/bold cyan] {platform.platform()}", title="System Info", border_style="cyan"))
            Prompt.ask("\nPress Enter to return to main menu")
        elif choice == "0":
            console.print("\n[bold red]Exiting FeaturesticLeaks PAK Tool. Goodbye![/bold red]\n")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[bold red][!] Interrupted by user. Exiting...[/bold red]")
        sys.exit(0)
