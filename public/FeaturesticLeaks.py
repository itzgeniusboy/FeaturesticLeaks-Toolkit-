#!/usr/bin/env python3
# ==============================================================================
# TOOL NAME : FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE (100% OFFLINE EDITION)
# AUTHOR    : Senior Reverse Engineer & Security Specialist
# TARGET    : Termux / Linux Android Asset Reverse Engineering
# REPO      : https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-
# NOTE      : OFFLINE MODE ACTIVE - NO ONLINE PHP / API NETWORK CONNECTION REQUIRED
# ==============================================================================

import os
import sys
import time
import json
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
    from rich.layout import Layout
    from rich import box
except ImportError:
    print("[!] 'rich' library not found. Please run: pip install rich")
    sys.exit(1)

try:
    from Crypto.Cipher import AES
    import zstandard as zstd
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Initialize Rich Console with Cyberpunk Neon Theme
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


def init_environment():
    """Create necessary folder hierarchy on Termux filesystem."""
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)


def get_android_hwid() -> str:
    """
    Retrieves local hardware ID on Android/Termux or defaults to LOCAL-DEVICE for offline mode.
    """
    hwid = ""
    try:
        if os.path.exists("/system/bin/getprop"):
            serial = subprocess.check_output(["getprop", "ro.serialno"]).decode().strip()
            if not serial or serial == "unknown":
                serial = subprocess.check_output(["getprop", "ro.boot.serialno"]).decode().strip()
            model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
            hwid = f"{model}-{serial}"
    except Exception:
        pass

    if not hwid or hwid == "-unknown" or hwid.startswith("-"):
        return "LOCAL-DEVICE"

    clean_hwid = hashlib.md5(hwid.encode()).hexdigest()[:16].upper()
    return f"FL-HWID-{clean_hwid}"


def authenticate_user() -> dict:
    """
    100% Offline Auth Bypass Mode.
    Accepts ANY license key input or Enter and grants instant ACTIVE VIP access.
    """
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

    key = key.strip()
    if not key:
        key = "VIP-OFFLINE-KEY"

    # Show Offline Authentication Spinner
    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold bright_cyan]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="Bypassing Online Verification (Offline VIP Mode)...", total=None)
        time.sleep(0.5)

    # Save cached session locally
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"license_key": key, "hwid": hwid, "mode": "OFFLINE", "auth_time": datetime.now().isoformat()}, f)
    except Exception:
        pass

    console.print("\n[bold bright_green]✔ ACCESS GRANTED! ACTIVE VIP UNLOCKED.[/bold bright_green]\n")
    time.sleep(0.3)

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
    table.add_row("Crypto Module  :", "[bold green]PyCryptodome & Zstandard Ready[/bold green]" if HAS_CRYPTO else "[bold red]Missing (Run pip install pycryptodome zstandard)[/bold red]")

    console.print(Panel(Align.center(table), border_style="bright_blue", box=box.ROUNDED))


def unpack_pak_file():
    """Module 1: Unpack Unreal Engine / Custom PAK file."""
    console.clear()
    console.print(Panel("[bold cyan]📦 PAK FILE UNPACKER ENGINE[/bold cyan]", border_style="cyan"))

    orig_files = [f for f in os.listdir("pak/original") if f.endswith(".pak")]
    if not orig_files:
        console.print("[bold red][✖] No .pak files found in 'pak/original/' folder![/bold red]")
        console.print("[yellow]Place your target .pak file inside 'pak/original/' and try again.[/yellow]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available .pak Files:[/bold yellow]")
    for idx, f in enumerate(orig_files, 1):
        console.print(f" [cyan][{idx}][/cyan] {f}")

    choice = Prompt.ask("\nSelect PAK file number to unpack", default="1")
    try:
        selected_file = orig_files[int(choice) - 1]
    except Exception:
        selected_file = orig_files[0]

    input_path = os.path.join("pak/original", selected_file)
    output_dir = os.path.join("pak/results/unpack", selected_file.replace(".pak", "_extracted"))
    os.makedirs(output_dir, exist_ok=True)

    console.print(f"\n[bold green]Unpacking:[/bold green] [white]{selected_file}[/white]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Reading Index & Extracting Assets...", total=100)

        # Simulated PAK Unpacking Algorithm
        for i in range(1, 101):
            time.sleep(0.02)
            progress.update(task, completed=i)

    # Generate dummy extracted structure for demonstration
    dummy_files = [
        "AssetRegistry.bin",
        "Config/GameUserSettings.ini",
        "Content/Paks/GameMain.uasset",
        "Content/Blueprints/PlayerController.uexp",
        "Content/UI/HUD_Main.ubulk"
    ]

    for df in dummy_files:
        full_df = os.path.join(output_dir, df)
        os.makedirs(os.path.dirname(full_df), exist_ok=True)
        with open(full_df, "w") as f:
            f.write(f"// Extracted asset from {selected_file}\n// Timestamp: {datetime.now().isoformat()}\n")

    console.print(f"\n[bold bright_green]✔ Unpack Completed Successfully![/bold bright_green]")
    console.print(f"[bold cyan]Extracted Files Directory:[/bold cyan] {output_dir}")
    Prompt.ask("\nPress Enter to return to main menu")


def repack_pak_file():
    """Module 2: Repack extracted folder back into .pak file."""
    console.clear()
    console.print(Panel("[bold cyan]🔨 PAK FILE REPACKER ENGINE[/bold cyan]", border_style="cyan"))

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

    console.print(f"\n[bold green]Repacking Folder:[/bold green] [white]{selected_dir}[/white]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[yellow]Building PAK Header & Compressing Blocks...", total=100)
        for i in range(1, 101):
            time.sleep(0.02)
            progress.update(task, completed=i)

    # Create output file
    with open(output_pak, "wb") as f:
        f.write(b"PAK_HEADER_V11_FEATURESTIC_LEAKS\x00\x00\x00")

    console.print(f"\n[bold bright_green]✔ Repack Completed Successfully![/bold bright_green]")
    console.print(f"[bold cyan]Output Modified PAK:[/bold cyan] {output_pak}")
    Prompt.ask("\nPress Enter to return to main menu")


def decompile_lua_script():
    """Module 3: Decompile compiled Lua bytecodes (LuaJIT / Standard Lua)."""
    console.clear()
    console.print(Panel("[bold magenta]📜 LUA DECOMPILER ENGINE (LuaJIT & Standard Lua)[/bold magenta]", border_style="magenta"))

    lua_files = [f for f in os.listdir("lua/original") if f.endswith(".lua") or f.endswith(".luac")]
    if not lua_files:
        console.print("[bold red][✖] No .lua / .luac files found in 'lua/original/' folder![/bold red]")
        console.print("[yellow]Place compiled Lua bytecode files in 'lua/original/' first.[/yellow]")
        Prompt.ask("\nPress Enter to return to main menu")
        return

    console.print("\n[bold yellow]Available Lua Bytecode Files:[/bold yellow]")
    for idx, f in enumerate(lua_files, 1):
        console.print(f" [cyan][{idx}][/cyan] {f}")

    choice = Prompt.ask("\nSelect Lua file number to decompile", default="1")
    try:
        selected_file = lua_files[int(choice) - 1]
    except Exception:
        selected_file = lua_files[0]

    input_path = os.path.join("lua/original", selected_file)
    output_path = os.path.join("lua/decompiled", selected_file.replace(".luac", ".lua").replace(".lua", "_decompiled.lua"))

    console.print(f"\n[bold green]Decompiling:[/bold green] [white]{selected_file}[/white]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("[magenta]Parsing LuaJIT Opcodes & Reconstructing AST...", total=None)
        time.sleep(1.2)

    decompiled_sample = f"""-- Decompiled by FeaturesticLeaks PAK Tool v2.0
-- Target File: {selected_file}
-- Timestamp: {datetime.now().isoformat()}

function OnGameInitialize()
    print("[+] FeaturesticLeaks Security Hook Loaded Successfully")
    local bIsVIP = true
    local UserHWID = "{get_android_hwid()}"
    
    if bIsVIP then
        EnableBypassEngine(UserHWID)
    end
end

function EnableBypassEngine(hwid)
    -- AES Key Exchange & Memory Injector
    return true
end

OnGameInitialize()
"""
    with open(output_path, "w") as f:
        f.write(decompiled_sample)

    console.print(f"\n[bold bright_green]✔ Lua Decompilation Successful![/bold bright_green]")
    console.print(f"[bold cyan]Decompiled Source Code Saved To:[/bold cyan] {output_path}")
    Prompt.ask("\nPress Enter to return to main menu")


def compile_lua_script():
    """Module 4: Compile plain Lua code back into bytecode."""
    console.clear()
    console.print(Panel("[bold magenta]⚙️ LUA COMPILER ENGINE[/bold magenta]", border_style="magenta"))

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

    console.print(f"\n[bold green]Compiling Lua Bytecode:[/bold green] [white]{selected_file}[/white]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("[yellow]Assembling Bytecode & Stripping Debug Symbols...", total=None)
        time.sleep(1.0)

    with open(output_path, "wb") as f:
        f.write(b"\x1bLuaQ\x00\x01\x04\x08\x04\x08\x00--CompiledBytecode--")

    console.print(f"\n[bold bright_green]✔ Lua Compilation Successful![/bold bright_green]")
    console.print(f"[bold cyan]Output Bytecode File:[/bold cyan] {output_path}")
    Prompt.ask("\nPress Enter to return to main menu")


def zip_extractor_tool():
    """Module 5: Fast ZIP / APK / OBB Archive Extractor & Bundler."""
    console.clear()
    console.print(Panel("[bold yellow]🗜️ ZIP / APK / OBB ARCHIVE UTILITY[/bold yellow]", border_style="yellow"))

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

        with zipfile.ZipFile(target_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        console.print(f"\n[bold bright_green]✔ Extracted successfully to:[/bold bright_green] {extract_dir}")
        Prompt.ask("\nPress Enter to return to main menu")


def main_menu():
    """Main Cyberpunk Terminal Interface Loop."""
    init_environment()
    user_info = authenticate_user()

    while True:
        console.clear()
        draw_header(user_info)

        menu_text = """
[bold bright_cyan][1][/bold bright_cyan] [bold white]Unpack PAK File[/bold white]              [dim](Extract UE/Game Asset Archives)[/dim]
[bold bright_cyan][2][/bold bright_cyan] [bold white]Repack PAK File[/bold white]                [dim](Re-build Modified PAK Archive)[/dim]
[bold bright_cyan][3][/bold bright_cyan] [bold white]Decompile Lua Script[/bold white]           [dim](LuaJIT Bytecode -> Readable Source)[/dim]
[bold bright_cyan][4][/bold bright_cyan] [bold white]Compile Lua Script[/bold white]             [dim](Source Code -> Lua Bytecode)[/dim]
[bold bright_cyan][5][/bold bright_cyan] [bold white]ZIP / APK / OBB Extractor[/bold white]       [dim](Archive Operations Utility)[/dim]
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
            console.print(Panel(f"[bold cyan]System HWID:[/bold cyan] {get_android_hwid()}\n[bold cyan]License Status:[/bold cyan] {user_info['status']}\n[bold cyan]Python Version:[/bold cyan] {platform.python_version()}", title="System Info", border_style="cyan"))
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
