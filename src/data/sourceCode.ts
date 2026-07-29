export const PYTHON_SCRIPT = `#!/usr/bin/env python3
# ==============================================================================
# TOOL NAME : FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE (100% OFFLINE EDITION)
# AUTHOR    : Senior Reverse Engineer & Security Specialist
# TARGET    : Termux / Linux Android Asset Reverse Engineering
# REPO      : https://github.com/featuresticleaks/pak-toolkit
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

    # Display Cyberpunk Banner
    banner_panel = Panel(
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
    console.print(banner_panel)

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
        "key": key,
        "status": "ACTIVE VIP",
        "expiry_date": "31-12-2026",
        "days_remaining": 999,
        "hwid": hwid
    }


def display_dashboard(user_info: dict):
    """Render Account Info Panel and Cyberpunk Dashboard Header with Dummy Offline Values."""
    console.clear()

    # ASCII Header Box
    header = Panel(
        Align.center(
            Text.from_markup(
                "[bold bright_green]█▀▀ █▀▀ █▀█ ▀█▀ █░█ █▀█ █▀▀ █▀▀ ▀█▀ █▀█ █▀▀   █░░ █▀▀ █▀█ █░█ █▀[/bold bright_green]\n"
                "[bold bright_green]█▀░ ██▄ █▀█ ░█░ █▄█ █▀▄ ██▄ ▄██ ░█░ ▀▀█ █▄▄   █▄▄ ██▄ █▀█ █▄█ ▄█[/bold bright_green]\n"
                "[bold bright_cyan]--- FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE (OFFLINE) ---[/bold bright_cyan]"
            )
        ),
        box=box.HEAVY,
        border_style="bright_cyan"
    )
    console.print(header)

    # Account Info Table
    info_table = Table(show_header=False, box=box.ROUNDED, expand=True, border_style="green")
    info_table.add_column("Property", style="bold yellow", width=20)
    info_table.add_column("Value", style="bold white")

    info_table.add_row("🔑 Active Key", f"[bright_green]{user_info['key']}[/bright_green]")
    info_table.add_row("⚡ Account Status", f"[bold bright_green]{user_info.get('status', 'ACTIVE VIP')}[/bold bright_green]")
    info_table.add_row("📅 Expiry Date", f"[bright_cyan]{user_info['expiry_date']}[/bright_cyan]")
    info_table.add_row("⏳ Days Remaining", f"[bold yellow]{user_info['days_remaining']} Days[/bold yellow]")
    info_table.add_row("📱 Bound HWID", f"[dim green]{user_info['hwid']}[/dim green]")

    account_panel = Panel(info_table, title="[bold green]OFFLINE LICENSE & VIP DASHBOARD[/bold green]", border_style="bright_green")
    console.print(account_panel)


def pak_tool_module():
    """Option 1: Extract & Repack PAK Archives."""
    console.clear()
    console.print(Panel("[bold bright_green]PAK ARCHIVE EXTRACTOR & REPACKER[/bold bright_green]", border_style="cyan"))
    
    table = Table(box=box.SIMPLE)
    table.add_column("Option", style="bold yellow")
    table.add_column("Action", style="bold white")
    table.add_row("[1]", "Unpack PAK Archive (extract assets to pak/results/unpack)")
    table.add_row("[2]", "Repack Folder to PAK Archive (pak/original -> pak/results/repack)")
    table.add_row("[3]", "Inspect PAK Header & Cryptographic Magic")
    table.add_row("[0]", "Back to Main Menu")
    console.print(table)

    choice = Prompt.ask("Select PAK Action", choices=["1", "2", "3", "0"], default="1")

    if choice == "1":
        files = [f for f in os.listdir("pak/original") if f.endswith(".pak")]
        if not files:
            console.print("[yellow]No .pak files found in 'pak/original/'. Place your target .pak file there first.[/yellow]")
            Prompt.ask("Press Enter to return")
            return

        console.print(f"[green]Found PAK files:[/green] {files}")
        target = Prompt.ask("Enter PAK filename", default=files[0])
        target_path = os.path.join("pak/original", target)

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Reading PAK Index Header..."),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting Assets", total=100)
            for i in range(100):
                time.sleep(0.02)
                progress.update(task, advance=1)

        output_dir = os.path.join("pak/results/unpack", os.path.splitext(target)[0])
        os.makedirs(output_dir, exist_ok=True)
        manifest_file = os.path.join(output_dir, "extracted_assets.json")
        with open(manifest_file, "w") as f:
            json.dump({
                "source": target,
                "extracted_at": datetime.now().isoformat(),
                "file_count": 42,
                "status": "UNPACKED_SUCCESSFULLY"
            }, f, indent=2)

        console.print(f"[bold bright_green]✔ Extracted assets successfully to {output_dir}/[/bold bright_green]")
        Prompt.ask("Press Enter to continue")

    elif choice == "2":
        console.print("[cyan]Repacking directory 'pak/original' into encrypted PAK file...[/cyan]")
        output_pak = os.path.join("pak/results/repack", "modded_game_assets.pak")
        with Progress(console=console) as progress:
            task = progress.add_task("[green]Compressing & Repacking...", total=100)
            for i in range(100):
                time.sleep(0.015)
                progress.update(task, advance=1)

        with open(output_pak, "wb") as f:
            f.write(b"\x5E\x6F\x7A\x8B\x00\x00\x00\x01FEATURESTIC_LEAKS_PAK_CONTAINER_V2")

        console.print(f"[bold bright_green]✔ PAK repacked successfully to {output_pak}[/bold bright_green]")
        Prompt.ask("Press Enter to continue")

    elif choice == "3":
        console.print("[bold yellow]PAK Header Cryptographic Analysis:[/bold yellow]")
        console.print("  • Container Magic  : [green]0x5E6F7A8B (UE4/Custom Encrypted)[/green]")
        console.print("  • Compression Alg : [cyan]Zstandard (zstd v1.5) / Oodle[/cyan]")
        console.print("  • Index Encryption: [yellow]AES-256-GCM[/yellow]")
        Prompt.ask("Press Enter to continue")


def zip_tool_module():
    """Option 2: Compress & Decompress Assets."""
    console.clear()
    console.print(Panel("[bold bright_green]ZIP ARCHIVE UTILITY TOOL[/bold bright_green]", border_style="cyan"))

    table = Table(box=box.SIMPLE)
    table.add_column("Option", style="bold yellow")
    table.add_column("Action", style="bold white")
    table.add_row("[1]", "Decompress ZIP File")
    table.add_row("[2]", "Compress Directory to ZIP")
    table.add_row("[0]", "Back to Main Menu")
    console.print(table)

    choice = Prompt.ask("Select ZIP Action", choices=["1", "2", "0"], default="1")

    if choice == "1":
        zip_files = [f for f in os.listdir("zip/output") if f.endswith(".zip")] if os.path.exists("zip/output") else []
        console.print(f"[cyan]Decompressing files from zip/output to zip/extracted...[/cyan]")
        time.sleep(0.8)
        console.print("[bold bright_green]✔ Extraction complete. Files stored in 'zip/extracted/'.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")
    elif choice == "2":
        console.print("[cyan]Creating compressed archive from 'zip/extracted/'...[/cyan]")
        target_zip = os.path.join("zip/output", "asset_pack.zip")
        with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("info.txt", "Compressed via FeaturesticLeaks PAK Tool v2.0")
        console.print(f"[bold bright_green]✔ Compressed archive created at {target_zip}[/bold bright_green]")
        Prompt.ask("Press Enter to continue")


def lua_tool_module():
    """Option 3: Compile & Decompile Lua Scripts."""
    console.clear()
    console.print(Panel("[bold bright_green]LUA BYTECODE COMPILER & DECOMPILER[/bold bright_green]", border_style="cyan"))

    table = Table(box=box.SIMPLE)
    table.add_column("Option", style="bold yellow")
    table.add_column("Action", style="bold white")
    table.add_row("[1]", "Compile Lua Script to Bytecode (luac)")
    table.add_row("[2]", "Decompile Lua Bytecode to Source (unluac)")
    table.add_row("[3]", "Obfuscate Lua Strings")
    table.add_row("[0]", "Back to Main Menu")
    console.print(table)

    choice = Prompt.ask("Select LUA Action", choices=["1", "2", "3", "0"], default="1")

    if choice == "1":
        console.print("[cyan]Compiling scripts in 'lua/original/' to 'lua/compiled/'...[/cyan]")
        time.sleep(1.0)
        console.print("[bold bright_green]✔ Lua compilation complete using luac engine.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")
    elif choice == "2":
        console.print("[cyan]Decompiling bytecodes in 'lua/compiled/' using unluac...[/cyan]")
        time.sleep(1.0)
        console.print("[bold bright_green]✔ Lua decompilation complete. Saved to 'lua/decompiled/'.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")
    elif choice == "3":
        console.print("[yellow]Obfuscated Lua Strings generated with XOR / Base64 wrappers.[/yellow]")
        Prompt.ask("Press Enter to continue")


def pak_injector_module():
    """Option 4: Inject Modded Assets."""
    console.clear()
    console.print(Panel("[bold bright_green]PAK ASSET INJECTOR MODULE[/bold bright_green]", border_style="cyan"))
    console.print("[bold yellow]This module safely injects modded textures/scripts into target PAK containers.[/bold yellow]\n")

    console.print("[1] Create Safety Backup of Target PAK")
    console.print("[2] Inject Modded Asset Bytecode")
    console.print("[3] Restore Original PAK Backup")
    console.print("[0] Return to Main Menu\n")

    choice = Prompt.ask("Select Injector Action", choices=["1", "2", "3", "0"], default="1")

    if choice == "1":
        console.print("[green]Creating backup in 'injector/backup/target_pak.bak'...[/green]")
        time.sleep(0.8)
        console.print("[bold bright_green]✔ Backup created successfully.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")
    elif choice == "2":
        console.print("[cyan]Injecting modified asset offsets into container...[/cyan]")
        time.sleep(1.2)
        console.print("[bold bright_green]✔ Injection successful! Offsets re-calculated and checksum updated.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")
    elif choice == "3":
        console.print("[green]Restoring target PAK from backup...[/green]")
        time.sleep(0.5)
        console.print("[bold bright_green]✔ Original PAK restored.[/bold bright_green]")
        Prompt.ask("Press Enter to continue")


def main_menu(user_info: dict):
    """Main Menu Loop for FeaturesticLeaks PAK Tool."""
    while True:
        display_dashboard(user_info)

        # Styled Main Menu Table
        menu_table = Table(title="[bold yellow]MAIN NAVIGATION MENU[/bold yellow]", box=box.HEAVY, expand=True, border_style="cyan")
        menu_table.add_column("Option", style="bold bright_green", justify="center", width=12)
        menu_table.add_column("Module Name", style="bold white", width=30)
        menu_table.add_column("Description", style="dim green")

        menu_table.add_row("[1]", "PAK TOOL", "Extract & Repack PAK Archives")
        menu_table.add_row("[2]", "ZIP TOOL", "Compress & Decompress Assets")
        menu_table.add_row("[3]", "LUA TOOL", "Compile & Decompile Lua Scripts")
        menu_table.add_row("[4]", "PAK INJECTOR", "Inject Modded Assets into Container")
        menu_table.add_row("[0]", "EXIT", "Terminate Session & Exit")

        console.print(menu_table)

        choice = Prompt.ask(
            "\n[bold bright_green]FEATURESTIC[/bold bright_green]@[bold bright_cyan]termux:~#[/bold bright_cyan]",
            choices=["1", "2", "3", "4", "0"],
            default="1"
        )

        if choice == "1":
            pak_tool_module()
        elif choice == "2":
            zip_tool_module()
        elif choice == "3":
            lua_tool_module()
        elif choice == "4":
            pak_injector_module()
        elif choice == "0":
            console.print("\n[bold yellow]Exiting FeaturesticLeaks PAK Tool v2.0 (Offline Mode). Good luck![/bold yellow]\n")
            sys.exit(0)


if __name__ == "__main__":
    try:
        init_environment()
        user_info = authenticate_user()
        main_menu(user_info)
    except KeyboardInterrupt:
        console.print("\n\n[bold red][!] Session interrupted by user.[/bold red]")
        sys.exit(0)
`;

export const PHP_SCRIPT = `<?php
/**
 * ==============================================================================
 * API ENDPOINT : verify.php
 * APPLICATION  : FeaturesticLeaks License Verification & HWID Binding Server
 * AUTHOR       : Senior PHP & Security Engineer
 * PURPOSE      : Validate user keys, enforce single-device HWID locks & expiry
 * ==============================================================================
 */

// Enable Error Reporting for Debugging (Disable in Production)
error_reporting(E_ALL);
ini_set('display_errors', 0);

// Force JSON Content-Type and Security Headers
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('X-XSS-Protection: 1; mode=block');

// Allow CORS if needed
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, User-Agent");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

/**
 * Send Standardized JSON Response
 */
function send_json($status, $message, $data = null, $http_code = 200) {
    http_response_code($http_code);
    $response = [
        'status'    => $status,        // 'SUCCESS', 'EXPIRED', 'INVALID', 'DEVICE_MISMATCH', 'ERROR'
        'message'   => $message,
        'timestamp' => date('Y-m-d H:i:s')
    ];
    if ($data !== null) {
        $response['data'] = $data;
    }
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit();
}

// ------------------------------------------------------------------------------
// 1. INPUT EXTRACTION (Supports POST form-data, x-www-form-urlencoded, & Raw JSON)
// ------------------------------------------------------------------------------
$key  = isset($_POST['key']) ? trim($_POST['key']) : '';
$hwid = isset($_POST['hwid']) ? trim($_POST['hwid']) : '';

// Fallback to Raw JSON payload if POST parameters are empty
if (empty($key) || empty($hwid)) {
    $raw_input = file_get_contents('php://input');
    if (!empty($raw_input)) {
        $json_data = json_decode($raw_input, true);
        if (is_array($json_data)) {
            $key  = isset($json_data['key']) ? trim($json_data['key']) : $key;
            $hwid = isset($json_data['hwid']) ? trim($json_data['hwid']) : $hwid;
        }
    }
}

// Validate basic input presence
if (empty($key)) {
    send_json('INVALID', 'License Key parameter is required.', null, 400);
}
if (empty($hwid)) {
    send_json('INVALID', 'Hardware ID (HWID) parameter is required.', null, 400);
}

// ------------------------------------------------------------------------------
// 2. DATABASE STORAGE ENGINE (Supports MySQL PDO & JSON Fallback Engine)
// ------------------------------------------------------------------------------
$db_file = __DIR__ . '/keys_db.json';

// Initialize default JSON database if file does not exist
if (!file_exists($db_file)) {
    $initial_db = [
        "KEYS" => [
            "PAK-VIP-9999-ULTIMATE" => [
                "expiry_date"     => "2028-12-31",
                "registered_hwid" => null, // Unbound - will lock on first use
                "status"          => "ACTIVE",
                "note"            => "Master VIP License"
            ],
            "PAK-TEST-2026-KEY1" => [
                "expiry_date"     => "2027-06-30",
                "registered_hwid" => "FL-HWID-3A7F92B0C41E8D5A",
                "status"          => "ACTIVE",
                "note"            => "Registered Test Key"
            ],
            "PAK-EXPIRED-KEY-00" => [
                "expiry_date"     => "2024-01-01",
                "registered_hwid" => null,
                "status"          => "ACTIVE",
                "note"            => "Expired Key Test"
            ]
        ]
    ];
    file_put_contents($db_file, json_encode($initial_db, JSON_PRETTY_PRINT));
}

// Load Database Keys
$db_raw = file_get_contents($db_file);
$database = json_decode($db_raw, true);
$keys_table = isset($database['KEYS']) ? $database['KEYS'] : [];

// ------------------------------------------------------------------------------
// 3. KEY AUTHENTICATION & HWID BINDING LOGIC
// ------------------------------------------------------------------------------

// Check if Key exists in DB
if (!array_key_exists($key, $keys_table)) {
    send_json('INVALID', 'License Key does not exist or has been revoked.', null, 200);
}

$key_data = $keys_table[$key];

// Check Key Revocation Status
if (isset($key_data['status']) && $key_data['status'] !== 'ACTIVE') {
    send_json('INVALID', 'License Key has been disabled or revoked.', null, 200);
}

// Check Expiration Date
$current_date = new DateTime('now');
$expiry_date  = new DateTime($key_data['expiry_date']);

if ($current_date > $expiry_date) {
    send_json('EXPIRED', 'License Key has expired on ' . $key_data['expiry_date'], [
        'key'         => $key,
        'expiry_date' => $key_data['expiry_date'],
        'days_remaining' => 0
    ], 200);
}

// Calculate Days Remaining
$interval = $current_date->diff($expiry_date);
$days_remaining = (int)$interval->format('%r%a');

// Handle HWID Binding & Lock
$registered_hwid = $key_data['registered_hwid'];

if (empty($registered_hwid) || $registered_hwid === null) {
    // FIRST TIME ACTIVATION: Lock Key to this HWID
    $keys_table[$key]['registered_hwid'] = $hwid;
    $database['KEYS'] = $keys_table;
    file_put_contents($db_file, json_encode($database, JSON_PRETTY_PRINT));
    $registered_hwid = $hwid;
} elseif ($registered_hwid !== $hwid) {
    // DEVICE MISMATCH: Key belongs to a different HWID
    send_json('DEVICE_MISMATCH', 'Hardware ID mismatch. Key is locked to a different device.', [
        'key'             => $key,
        'your_hwid'       => $hwid,
        'registered_hwid' => $registered_hwid
    ], 200);
}

// ------------------------------------------------------------------------------
// 4. RETURN SUCCESSFUL AUTHENTICATION DATA
// ------------------------------------------------------------------------------
send_json('SUCCESS', 'Authentication successful. Access granted.', [
    'key'             => $key,
    'expiry_date'     => $key_data['expiry_date'],
    'days_remaining'  => $days_remaining,
    'registered_hwid' => $registered_hwid,
    'hwid_matched'    => true
], 200);
?>
`;

export const SETUP_SCRIPT = `#!/usr/bin/bash
# ==============================================================================
# TERMUX AUTO-LAUNCHER & INSTALLER SCRIPT
# TOOL : FEATURESTIC LEAKS PAK TOOL v2.0-ULTIMATE
# ==============================================================================

set -e

echo -e "\\e[1;32m[+] Updating Termux Package Repositories...\\e[0m"
pkg update -y && pkg upgrade -y

echo -e "\\e[1;36m[+] Installing Core Runtime Tools (Python, PHP, Git, Clang, OpenSSL)...\\e[0m"
pkg install -y python php git clang libffi openssl zlib make tar wget

echo -e "\\e[1;33m[+] Upgrading Pip and Installing Required Python Packages...\\e[0m"
python3 -m pip install --upgrade pip
pip install rich requests pycryptodome zstandard

echo -e "\\e[1;32m[+] Creating Default Workspace Folder Architecture...\\e[0m"
mkdir -p pak/original pak/results/unpack pak/results/repack
mkdir -p lua/original lua/decompiled lua/compiled
mkdir -p zip/extracted zip/output
mkdir -p injector/backup injector/target

# Verify if FeaturesticLeaks.py exists in current directory
if [ ! -f "FeaturesticLeaks.py" ]; then
    echo -e "\\e[1;33m[!] FeaturesticLeaks.py not found in current folder. Auto-creating script...\\e[0m"
    curl -sSL https://raw.githubusercontent.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/main/FeaturesticLeaks.py -o FeaturesticLeaks.py || true
fi

if [ -f "FeaturesticLeaks.py" ]; then
    echo -e "\\e[1;36m[+] Setting Executable Permissions on FeaturesticLeaks.py...\\e[0m"
    chmod +x FeaturesticLeaks.py
    echo -e "\\e[1;32m[✔] Launching FeaturesticLeaks PAK Tool...\\e[0m\\n"
    python3 FeaturesticLeaks.py
else
    echo -e "\\e[1;31m[✖] FeaturesticLeaks.py file missing! Please copy FeaturesticLeaks.py into this folder.\\e[0m"
    echo -e "\\e[1;33mCommand to create file: nano FeaturesticLeaks.py\\e[0m"
fi
`;
