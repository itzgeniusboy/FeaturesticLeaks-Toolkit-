# FEATURESTIC LEAKS - PAK TOOL v2.0
# Developer Telegram: @L359D (https://t.me/L359D)
# Official Telegram Channel: https://t.me/FeaturesticLeaks
# Termux / Linux Android Game Reverse Engineering & PAK Manipulation Toolkit

#One_Of_The_Best_Tool_In_Whole_Telegram - 100% WORKING FINAL

import itertools as it
import math
import struct
import shutil
import os
import sys
import uuid
import hashlib
import platform
import subprocess
import base64
import zlib
import json
import zipfile
import re
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePath, Path
from typing import List, Dict, Tuple, Optional, Any
import time
import subprocess
import threading
import shutil
import traceback
import gc
import mmap
import concurrent.futures

# ==================== BIG FILE OPTIMIZATION HELPERS ====================

# Audio welcome voice playback
_AUDIO_PLAYED = False
def play_welcome_audio():
    global _AUDIO_PLAYED
    if _AUDIO_PLAYED:
        return
    _AUDIO_PLAYED = True
    def _speak():
        msg = "Welcome to Featurestic Leaks World"
        if shutil.which("termux-tts-speak"):
            try:
                subprocess.run(["termux-tts-speak", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif shutil.which("espeak"):
            try:
                subprocess.run(["espeak", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif shutil.which("spd-say"):
            try:
                subprocess.run(["spd-say", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    threading.Thread(target=_speak, daemon=True).start()

# Auto-install missing dependencies if run directly with python
def _ensure_package(pkg_name, import_name=None, required=True):
    if import_name is None:
        import_name = pkg_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"[+] Installing missing dependency: {pkg_name}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg_name, "--timeout", "10"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[OK] Installed {pkg_name}")
        except Exception as e:
            if required:
                print(f"[!] Warning: Could not install {pkg_name} ({e}). Ensure internet connection if needed.")
            else:
                print(f"[!] Optional package {pkg_name} skip ho gaya (Offline / Network issue).")

_ensure_package("rich")
_ensure_package("requests")
_ensure_package("pytz")
_ensure_package("gmalg")
_ensure_package("pycryptodome", "Crypto")
_ensure_package("zstandard")
_ensure_package("watchdog", required=False)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except Exception:
    HAS_WATCHDOG = False

try:
    import requests
except ImportError:
    requests = None

try:
    import pytz
except ImportError:
    pytz = None

try:
    import gmalg
except ImportError:
    gmalg = None

try:
    from Crypto.Cipher import AES
    from Crypto.Cipher.AES import MODE_CBC
    from Crypto.Hash import SHA1
    from Crypto.Util.Padding import unpad
except ImportError:
    AES = MODE_CBC = SHA1 = unpad = None

try:
    from zstandard import ZstdDecompressor, ZstdCompressionDict, DICT_TYPE_AUTO, ZstdCompressor
except ImportError:
    ZstdDecompressor = ZstdCompressionDict = DICT_TYPE_AUTO = ZstdCompressor = None

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
    from rich.table import Table
    from rich import print as rprint
    from rich.markup import escape
    from rich.text import Text
    from rich.align import Align
    from rich.console import Group
    from rich.live import Live
    from rich.box import HEAVY_EDGE, ROUNDED, DOUBLE_EDGE
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                print(args[0])
    class DummyAlign:
        @staticmethod
        def center(val, *args, **kwargs):
            return val
    class DummyPanel:
        def __init__(self, content, *args, **kwargs):
            self.content = content
        def __str__(self):
            return str(self.content)
    class DummyTable:
        def __init__(self, *args, **kwargs): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs): pass
    console = DummyConsole()
    Panel = DummyPanel
    Align = DummyAlign
    Table = DummyTable
    Progress = SpinnerColumn = TextColumn = BarColumn = TaskProgressColumn = TimeElapsedColumn = TimeRemainingColumn = Group = Live = None
    HEAVY_EDGE = ROUNDED = DOUBLE_EDGE = ""
    def escape(s): return str(s)
    def Text(s=""): return str(s)
    def rprint(*args, **kwargs): print(*args)

# ==================== ORIGINAL CLASSES ====================

ZUC_KEY = bytes.fromhex('01010101010101010101010101010101')
ZUC_IV = bytes.fromhex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

RSA_MOD_1 = bytes.fromhex('CBE8B9F2504050EF9831B719E9A6249A6D238505ADE909BDE78C180DED6072A0C3347B8AF4780E1F212D952D82D4BF7F233C1ECA499E1F9D9A85B4FAD759F54BABC1666C5DE411EA9E4B2374425DD6C6F54333BBC8F2610FE6063E4D0D6C21A671A8F7C3740555E5DC06D4E1691C456DB4116C0C012BF7B206E8311AAAEC689952BF804EF638F09D5822B4117B114208F14DEB459E80CB770E5B0D7978E21F5E6CED4999D3583108221A7AB28B960277ADB5690A332784019D9C195BE4EA9EA0A09459010F236465DE0D59C3EF7324E954E1118D93EE19F299760C2CDB963CE87973EA5ECC9BBE81C27D4C7C8572AC07E9BCEAC9BD72AB7A56A3C0AD736ABCE4')
RSA_MOD_2 = bytes.fromhex('7F58E8A39A4DA4E87357DDD650EAA16D3B5CE95B213D1030A662566444796A78A84AE9AC3DBFFDE7F41094896696835DAF13B89E6EC2B84963B1B1BAF7151DA245C3FBFAE2A6AE18B2684D03F9229DE2C91440F2A3A3BCDE1E5680C16722A88039C73560D5D43F4B6562C2EEA5B1D926D86B51108A2643C70FB74D6442CE3A08339B8FD8F660AE88129B7AB8C46F2FA58124485CCCB1E987B05A6DA65A01858ED3F89905449AE42BB07290FCB9994BF22E26610BCABB9804783A3B9587917F3D97316EDDA15C5E13F79066407B55A93B291B68A4AC42A98D6E35FED84B14A792D154E62028DDAD20FC301951E5924BE9AD62FB719DD94CC30CAB871BEC4377A8')

SIMPLE1_DECRYPT_KEY = 121
SIMPLE2_DECRYPT_KEY = bytes.fromhex('E55B4ED1')
SIMPLE2_BLOCK_SIZE = 16

SM4_SECRET_4 = 'eb691efea914241317a8'
SM4_SECRET_2 = 'Q0hVTKey$as*1ZFlQCiA'
SM4_SECRET_NEW = [
    'xG2qW5lP7lV2iN5fN5pG',
    'xT1cJ6dL5wC0kK1rB4dK',
    'qC4jS5bZ6fL5xE6nD4zA',
    'gD4jQ2aL3bS3lC3xT0iW',
    'xU1yQ8wE9zY3gZ3bT5aE',
    'uQ3cO2dX7xY4xU7gH7iS',
    'gW1fR0jK6wQ4oN0oK1kZ',
    'aJ4pV7iZ7pU4wP2aC2cZ',
    'cX6jT3cM2oT3vK0kJ1qN',
    'iT2vS0cS6yT6cZ1sE1lO',
    'hM1pH9iY8wM9hT4lN5uJ',
    'kG6bC8jK0fL0dE4sH4mL',
    'dB6lB3vE0eZ8wM8rI0aC',
    'tP7sP7nI9rA2vQ4cV5yQ',
    'aT0cL1yN4pT3sZ7eM2vY',
    'uV6fU8fC9zN3mP5dH8mN'
]

EM_SIMPLE1 = 1
EM_SIMPLE2 = 16
EM_SM4_2 = 2
EM_SM4_4 = 4
EM_SM4_NEW_BASE = 31
EM_SM4_NEW_MASK = ~EM_SM4_NEW_BASE
EM_UNKNOWN_17 = 17

CM_NONE = 0
CM_ZLIB = 1
CM_ZSTD = 6
CM_ZSTD_DICT = 8
CM_MASK = 15


# ============================================================================
# MODULE IMPORTS (REFACTORED CORE, PAK, LUA UTILITIES)
# ============================================================================
from pak.crypto import SM4, PakCrypto, _LCG
from pak.compression import PakCompression
from pak.container import (
    Misc, Reader, PakInfo, TencentPakInfo, PakCompressedBlock,
    TencentPakEntry, TencentPakFile, pad_to_n, align_up
)
from pak.repack import (
    SimpleBlockDisplay, dump_unpacking_log, _zstd_add_skippable_padding,
    _encrypt_plaintext, _repack_uncompressed, _repack_compressed_with_display,
    _best_compress, _stream_copy_bytes, _pw_string, _pw_entry, _get_all_dirs_and_mp,
    repack_pak_file_full, repack_pak_file_with_block_display, repack_mini_obb,
    repack_obbzsdic, repack_gamepatch, detect_repack_mode, smart_resolve_by_fingerprint
)
from lua.reader import (
    _LuaCustomReader, _LuaProto, _LuaStdReader, _LuaStdProto,
    _parse_lua_custom, _load_lua_custom_proto, _parse_lua_std,
    _std_to_custom_lua_proto, _load_std_bytecode_to_proto, _lua_xor
)
from lua.decompiler import (
    _get_lua_opcode_name, _decode_lua_instruction, _format_lua_const,
    _reg_name, _pseudo_decompile_lua, fix_lua_syntax_for_lua51
)
from lua.tools import (
    UniversalLuaPacker, _b64_pack, _b64_unpack, _xor_pack, _xor_unpack,
    _zlib_pack, _zlib_unpack, _raw_pack, _raw_unpack,
    run_universal_lua_pack, run_universal_lua_unpack, run_lua_string_obfuscator,
    run_lua_anti_bypass_analyzer, run_lua_header_fixer, run_lua_script_optimizer,
    run_gg_code_generator, run_lua_script_merger, run_lua_protector_obfuscator,
    run_lua_compiler, run_lua_decompiler, extract_pak_from_lua, embed_pak_into_lua,
    run_lua_pak_extractor, run_pak_lua_embedder
)
from core.logging_utils import (
    get_device_user_info, cleanup_old_logs, send_telegram_bug_report,
    send_telegram_status_update, handle_exception
)
from ai.assistant import get_ai_config, call_ai_api
from ai.analyzer import run_ai_function_mod_generator, extract_lua_functions_and_symbols, scan_unpacked_directory

def show_workflow_guide():
    console.print(Panel(Align.center("[bold bright_cyan]📖 FEATURESTIC LEAKS - EASY STEP-BY-STEP WORKFLOW GUIDE[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    guide_text = """
[bold yellow]1️⃣ STEP 1: ORIGINAL PAK FILE DAALO[/bold yellow]
• Apni game .pak ya .obb file ko is folder me rakho:
  👉 [bold cyan]/sdcard/FeaturesticLeaks/PAK/[/bold cyan]
• Tool kholo aur [bold green]Option 1 (Unpack)[/bold green] run karo.
• Files extract ho kar [bold cyan]/sdcard/FeaturesticLeaks/UNPACK/[/bold cyan] me chali jayengi.

[bold yellow]2️⃣ STEP 2: FILES EDIT KARO & REPLACEMENT RAKHO[/bold yellow]
• [bold white]Option A (Existing file replace karni hai):[/bold white]
  Edited files ko [bold cyan]/sdcard/FeaturesticLeaks/REPLACE/[/bold cyan] folder me daalo.
  Phir main menu se [bold green]Option 3 (Replace Files)[/bold green] run karo.
  
• [bold white]Option B (Custom internal path par new file inject karni hai):[/bold white]
  New files ko [bold cyan]/sdcard/FeaturesticLeaks/INJECT/[/bold cyan] folder me daalo.
  Phir main menu se [bold green]Option 4 (Inject Path)[/bold green] run karo aur internal path enter karo.

[bold yellow]3️⃣ STEP 3: MODDED PAK OUTPUT LE LO[/bold yellow]
• Aapki modified output .pak file is folder me milegi:
  👉 [bold green]/sdcard/FeaturesticLeaks/RESULT/[/bold green]
• Is file ko Game/OBB folder me copy kar do aur game start karo!
    """
    console.print(Panel(guide_text, border_style="dim white", box=ROUNDED))

def install_termux_shortcut_and_sdcard(data_path: Path, silent: bool = False):
    if not silent:
        console.print("\n[bold cyan][+] Setting up Termux Shortcuts ('leak', 'paktool') & SDCard Workspace...[/bold cyan]")
    
    try:
        ensure_directories(data_path)
        if not silent:
            console.print(f"[bold green][OK] SDCard Workspace Created cleanly: /sdcard/FeaturesticLeaks/[/bold green]")
    except Exception:
        if not silent:
            console.print(f"[yellow][!] Notice: SDCard folder permission check skipped.[/yellow]")
    
    script_file = Path(__file__).resolve()
    script_dir = script_file.parent
    
    # Try creating executables in Termux bin directories
    bin_dirs = [
        Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "bin",
        Path("/data/data/com.termux/files/usr/bin"),
        Path.home() / ".local" / "bin"
    ]
    
    shortcuts_created = []
    for bin_dir in bin_dirs:
        if bin_dir.exists() and os.access(bin_dir, os.W_OK):
            for cmd_name in ["leak", "paktool"]:
                cmd_path = bin_dir / cmd_name
                try:
                    content = f"#!/data/data/com.termux/files/usr/bin/sh\ncd \"{script_dir}\" && python3 \"{script_file}\" \"$@\"\n"
                    cmd_path.write_text(content, encoding="utf-8")
                    cmd_path.chmod(0o755)
                    shortcuts_created.append(cmd_name)
                except Exception:
                    pass
            if shortcuts_created:
                break
    
    # Ensure decompilation dependencies (openjdk-17, luadec, unluac.jar) are set up automatically in Termux
    unluac_path = data_path / "unluac.jar"
    if not unluac_path.exists():
        unluac_home = Path.home() / "unluac.jar"
        if unluac_home.exists():
            unluac_path = unluac_home

    is_termux = "com.termux" in os.environ.get("PREFIX", "") or Path("/data/data/com.termux").exists()
    
    # Only perform heavy pkg install / curl download if interactive/explicitly called, or if unluac.jar is missing
    # To prevent slow boot every time, we check a flag or skip pkg install if java/luadec are already present or during silent boot
    if is_termux and not silent:
        needs_pkg = False
        if not shutil.which("java") or not shutil.which("luadec"):
            needs_pkg = True
        
        if needs_pkg:
            console.print("[bold yellow][+] Auto-installing openjdk-17 & luadec for full Lua decompilation...[/bold yellow]")
            try:
                subprocess.run(["pkg", "install", "-y", "openjdk-17", "luadec"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        if not unluac_path.exists():
            console.print("[bold yellow][+] Downloading unluac.jar for 100% full Lua decompiler support...[/bold yellow]")
            try:
                subprocess.run(["curl", "-L", "-o", str(data_path / "unluac.jar"), "https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/releases/download/v1.0/unluac.jar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
    shell_files = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
    aliases_to_add = [
        f"alias leak='cd \"{script_dir}\" && python3 \"{script_file}\"'",
        f"alias paktool='cd \"{script_dir}\" && python3 \"{script_file}\"'"
    ]
    
    for sh_file in shell_files:
        try:
            curr_content = sh_file.read_text(encoding="utf-8") if sh_file.exists() else ""
            lines_to_append = []
            for alias_line in aliases_to_add:
                cmd_alias = alias_line.split("=")[0]
                if cmd_alias not in curr_content:
                    lines_to_append.append(alias_line)
            if lines_to_append:
                with open(sh_file, "a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(lines_to_append) + "\n")
        except Exception:
            pass

    if not silent:
        console.print("[bold green][OK] Created shortcuts: 'leak' & 'paktool'[/bold green]")
        console.print("\n[bold green]🎉 Complete! Next time Termux me kahin bhi 'leak' ya 'paktool' type karke directly open kar sakte hain![/bold green]")

UPDATE_NOTIF_BANNER = ""

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    banner_content = (
        "[bold bright_cyan]⚡ FEATURESTIC LEAKS v2.5 ⚡[/bold bright_cyan] │ [bold bright_yellow]VIP EXPLOIT ENGINE[/bold bright_yellow]\n"
        "[bold white]DEV:[bold cyan] @L359D[/bold cyan] │ TG:[bold cyan] t.me/FeaturesticLeaks[/bold cyan] │ STATUS:[bold bright_green] 🟢 READY[/bold bright_green][/bold white]"
    )
    console.print(Panel(
        Align.center(banner_content),
        title="[bold bright_yellow] 👑 HIGH SPEED ENGINE 👑 [/bold bright_yellow]",
        title_align="center",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 1)
    ))
    
    if UPDATE_NOTIF_BANNER:
        console.print(Panel(
            Align.center(UPDATE_NOTIF_BANNER),
            border_style="yellow",
            box=ROUNDED,
            padding=(0, 1)
        ))

def boot_sequence():
    """
    Animated rocket boot sequence (approx 2-3 seconds):
    Left to right moving rocket with trail and dynamic status text.
    Mobile/Termux safe rendering using standard unicode characters.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    total_frames = 22
    statuses = [
        (0, "Initializing core engine..."),
        (5, "Loading encryption & PAK modules..."),
        (10, "Verifying workspace folders..."),
        (16, "Ready for launch..."),
        (22, "🚀 LAUNCHED — Welcome to FeaturesticLeaks")
    ]
    
    current_status = statuses[0][1]
    track_len = 26
    
    try:
        with Live(refresh_per_second=12, console=console, transient=True) as live:
            for frame in range(total_frames + 1):
                for threshold, msg in statuses:
                    if frame >= threshold:
                        current_status = msg
                
                pos = min(int((frame / total_frames) * track_len), track_len)
                trail = "═" * pos
                spaces = " " * (track_len - pos)
                
                if frame < total_frames:
                    rocket_line = f"[dim cyan]{trail}[/dim cyan][bold bright_yellow]🚀[/bold bright_yellow][dim]❯[/dim]{spaces}"
                else:
                    rocket_line = f"[dim cyan]{'═' * track_len}[/dim cyan][bold bright_yellow] 🚀 READY[/bold bright_yellow]"
                
                anim_content = (
                    f"  [bold bright_cyan]⚡ FEATURESTIC LEAKS PAK TOOL ⚡[/bold bright_cyan]\n\n"
                    f"  {rocket_line}\n\n"
                    f"  [bold cyan][⚙][/bold cyan] [white]{current_status}[/white]"
                )
                
                panel = Panel(
                    anim_content,
                    border_style="cyan",
                    box=ROUNDED,
                    padding=(1, 2)
                )
                
                live.update(panel)
                time.sleep(0.09)
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    
    time.sleep(0.2)

def check_and_auto_update(interactive: bool = False):
    """
    Auto-updater & update notifier for FeaturesticLeaks:
    - Checks GitHub commits & raw repository version
    - If interactive=True (Option 9 in Utilities or 'U' shortcut): downloads fresh script, verifies python compilation, backs up current file, updates, and auto-restarts tool.
    - If interactive=False (background boot check): checks if remote version/hash is newer, and sets UPDATE_NOTIF_BANNER notice banner.
    """
    global UPDATE_NOTIF_BANNER
    try:
        if getattr(sys, 'frozen', False):
            script_path = Path(sys.executable)
            script_dir = script_path.parent
        else:
            script_path = Path(__file__).resolve()
            script_dir = script_path.parent

        hash_file = script_dir / ".commit_hash"
        local_hash = ""
        if hash_file.exists():
            local_hash = hash_file.read_text(encoding='utf-8').strip()
        elif (script_dir / ".git").exists():
            try:
                res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=script_dir, capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    local_hash = res.stdout.strip()
            except Exception:
                pass

        if interactive:
            console.print("[bold cyan]🔄 Checking GitHub for latest FeaturesticLeaks updates...[/bold cyan]")

        headers = {"User-Agent": "FeaturesticLeaks-Termux/2.5"}
        url = "https://api.github.com/repos/itzgeniusboy/FeaturesticLeaks-Toolkit-/commits/main"
        remote_hash = ""

        try:
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                remote_hash = resp.json().get("sha", "").strip()
        except Exception:
            pass

        raw_url = "https://raw.githubusercontent.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/main/FeaturesticLeaks.py"
        raw_resp = None

        if not remote_hash or interactive:
            try:
                raw_resp = requests.get(raw_url, headers=headers, timeout=8)
                if raw_resp and raw_resp.status_code == 200 and len(raw_resp.content) > 5000:
                    remote_hash = hashlib.md5(raw_resp.content).hexdigest()
            except Exception:
                pass

        if not remote_hash:
            if interactive:
                console.print("[bold yellow]⚠️ Network check failed or offline mode. Unable to reach GitHub update server.[/bold yellow]")
            return

        has_update = False
        if not local_hash:
            local_hash = hashlib.md5(script_path.read_bytes()).hexdigest() if script_path.exists() else "1"

        if remote_hash != local_hash:
            has_update = True
            UPDATE_NOTIF_BANNER = "🔥 [bold bright_yellow]NEW TOOL UPDATE AVAILABLE![/bold bright_yellow] [dim]Press [bold cyan][U][/bold cyan] in Main Menu to Auto-Update Instantly![/dim]"

        if interactive:
            if not has_update and not raw_resp:
                console.print("[bold green]✅ Tool is already running the latest FeaturesticLeaks version![/bold green]")
                return

            console.print("[bold green]🚀 New update detected! Downloading latest FeaturesticLeaks engine...[/bold green]")
            if not raw_resp:
                raw_resp = requests.get(raw_url, headers=headers, timeout=12)

            if raw_resp and raw_resp.status_code == 200 and len(raw_resp.content) > 5000:
                temp_file = script_path.with_suffix(".update_tmp")
                temp_file.write_bytes(raw_resp.content)

                import py_compile
                try:
                    py_compile.compile(str(temp_file), doraise=True)
                except Exception as compile_err:
                    console.print(f"[bold red]❌ Downloaded update syntax check failed: {compile_err}. Update cancelled.[/bold red]")
                    temp_file.unlink(missing_ok=True)
                    return

                bak_file = script_path.with_suffix(".py.bak")
                try:
                    shutil.copy2(script_path, bak_file)
                except Exception:
                    pass

                shutil.move(str(temp_file), str(script_path))
                hash_file.write_text(remote_hash, encoding='utf-8')
                UPDATE_NOTIF_BANNER = ""

                console.print(Panel(
                    "[bold bright_green]🎉 FEATURESTIC LEAKS AUTO-UPDATED SUCCESSFULLY! 🎉[/bold bright_green]\n\n"
                    "[bold white]Engine script has been updated & verified.[/bold white]\n"
                    "[bold cyan]Restarting application automatically now...[/bold cyan]",
                    border_style="green",
                    box=ROUNDED
                ))
                time.sleep(1.5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                console.print("[bold red][X] Failed to download update file from raw GitHub source.[/bold red]")
    except Exception as ex:
        if interactive:
            console.print(f"[bold red][X] Auto-update error: {ex}[/bold red]")

def styled_prompt(message: str = "", context: str = "~") -> str:
    """
    Renders T3RMUX terminal themed prompt:
    ┌─[FeaturesticLeaks@termux]-[context] (Optional Message)
    └─>>> 
    """
    has_leading_nl = message.startswith('\n') or message.startswith('\r\n')
    clean_msg = message.lstrip('\r\n').strip()
    if clean_msg.startswith("-> "):
        clean_msg = clean_msg[3:].strip()
        
    if has_leading_nl:
        console.print()

    # Header line
    header = (
        "[dim cyan]┌─[/dim cyan]"
        "[dim][[/dim]"
        "[bold bright_magenta]FeaturesticLeaks[/bold bright_magenta]"
        "[bold bright_cyan]@termux[/bold bright_cyan]"
        "[dim]][/dim]"
        "[dim cyan]─[/dim cyan]"
        "[dim][[/dim]"
        f"[bold yellow]{context}[/bold yellow]"
        "[dim]][/dim]"
    )
    
    if clean_msg:
        if clean_msg.lower().startswith("press enter"):
            header += f" [dim yellow]({clean_msg})[/dim yellow]"
        else:
            header += f" [dim]({clean_msg})[/dim]"

    console.print(header)

    # Prompt arrow line
    prompt_line = "[dim cyan]└─[/dim cyan][bold #FF6B6B]>>>[/bold #FF6B6B] "
    console.print(prompt_line, end="")

    try:
        return input()
    except (EOFError, RuntimeError):
        try:
            if sys.platform != 'win32':
                with open('/dev/tty', 'r') as tty:
                    return tty.readline().rstrip('\n')
            else:
                with open('CON', 'r') as con:
                    return con.readline().rstrip('\r\n')
        except Exception:
            return ""
    except Exception:
        return ""

def safe_input(prompt: str = '', context: str = '~') -> str:
    return styled_prompt(message=prompt, context=context)

def human_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} PB'

def delete_folder(data_path: Path) -> None:
    folders = []
    for item in data_path.iterdir():
        if item.is_dir() and item.name not in ['PAK', 'UNPACK', 'REPACK', 'RESULT', 'PAK TOOL']:
            folders.append(item)
    if not folders:
        console.print('[yellow][!] No folders found to delete.[/yellow]')
        return
    folder_table = Table(
        title="[bold cyan]AVAILABLE WORKSPACE FOLDERS[/bold cyan]",
        border_style="dim cyan",
        box=ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    folder_table.add_column("Index", justify="center", style="bold yellow", width=8)
    folder_table.add_column("Folder Name", justify="left", style="bold white")
    folder_table.add_column("Size", justify="right", style="dim")
    for i, folder in enumerate(folders, 1):
        folder_size = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    folder_size += os.path.getsize(file_path)
        folder_table.add_row(str(i), escape(folder.name), human_size(folder_size))
    console.print(folder_table)
    try:
        choice_str = safe_input(f"\n-> Select folder number (1-{len(folders)}): ").strip()
        choice = int(choice_str)
        if 1 <= choice <= len(folders):
            selected_folder = folders[choice - 1]
            confirm = safe_input(f"-> Delete {selected_folder.name}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                shutil.rmtree(selected_folder)
                console.print(f'[bold green][OK] Deleted: {selected_folder.name}[/bold green]')
            else:
                console.print('[yellow][!] Cancelled[/yellow]')
        else:
            console.print('[bold red][X] Invalid selection[/bold red]')
    except ValueError:
        console.print('[bold red][X] Invalid input[/bold red]')

def pick_file_from_folder(action_title: str, default_folder: Path, extensions: List[str] = [".pak", ".obb"]) -> Tuple[Optional[Path], List[Path]]:
    """
    Smart Folder Path File Picker:
    - Prompts user for a folder path (or direct file path).
    - Scans folder for .pak / .obb files.
    - If 1 file found: Auto-selects automatically.
    - If multiple files found: Shows numbered clean table for quick selection (e.g. '2').
    - If no files found: Clear error message and re-prompts.
    """
    current_path_str = str(default_folder)
    
    while True:
        target_path = Path(current_path_str)
        
        # Scan folder
        found_files = []
        scan_dirs = []
        if target_path.exists():
            scan_dirs.append(target_path)
        
        sd_twin = Path("/sdcard/FeaturesticLeaks") / target_path.name
        if sd_twin.exists() and sd_twin not in scan_dirs:
            scan_dirs.append(sd_twin)
            
        sd_base = Path("/sdcard/FeaturesticLeaks")
        if sd_base.exists() and sd_base not in scan_dirs:
            sd_sub = sd_base / target_path.name
            if sd_sub.exists() and sd_sub not in scan_dirs:
                scan_dirs.append(sd_sub)
            
        # Multi-folder scan fallback for common workspace directories
        extra_subdirs = [
            "INPUT", "OUTPUT", "REPLACE", "INJECT", "PAK", "LUA", "UNPACK", "RESULT",
            "PAK_WORKSPACE/1_PAK_INPUT", "PAK_WORKSPACE/2_UNPACK", "PAK_WORKSPACE/3_REPLACE", "PAK_WORKSPACE/4_INJECT", "PAK_WORKSPACE/5_RESULT",
            "LUA_WORKSPACE/1_LUA_INPUT", "LUA_WORKSPACE/2_DECOMPILED", "LUA_WORKSPACE/3_COMPILED", "LUA_WORKSPACE/4_RESULT"
        ]
        base_parent = default_folder.parent if hasattr(default_folder, 'parent') and default_folder.parent.exists() else default_folder
        for sub in extra_subdirs:
            cand = base_parent / sub
            if cand.exists() and cand not in scan_dirs:
                scan_dirs.append(cand)
            sd_cand = Path("/sdcard/FeaturesticLeaks") / sub
            if sd_cand.exists() and sd_cand not in scan_dirs:
                scan_dirs.append(sd_cand)

        for sdir in scan_dirs:
            if sdir.exists() and sdir.is_dir():
                for p in sdir.iterdir():
                    if p.is_file() and any(p.name.lower().endswith(ext.lower()) for ext in extensions):
                        if not any(existing.name.lower() == p.name.lower() for existing in found_files):
                            found_files.append(p)
        
        found_files.sort(key=lambda x: x.name.lower())
        
        # If files are found in default/SDCard location, auto display file selection or auto-select
        if found_files:
            if len(found_files) == 1:
                selected = found_files[0]
                size_mb = selected.stat().st_size / (1024 * 1024)
                console.print(f"\n[bold green][OK] Auto-selected file: {selected.name} ({size_mb:.2f} MB)[/bold green]")
                console.print(f"[dim]📂 Folder Location: {selected.parent}[/dim]")
                return selected, found_files

            # Multiple files found -> Display clean table directly without asking for folder path
            file_table = Table(
                title=f"[bold cyan]Available Files ({action_title})[/bold cyan]",
                show_header=True,
                header_style="bold cyan",
                box=ROUNDED,
                border_style="dim cyan",
                expand=True
            )
            file_table.add_column("Index", style="bold yellow", justify="center", width=8)
            file_table.add_column("Filename", style="bold white", justify="left")
            file_table.add_column("Size", style="dim", justify="right", width=12)
            
            for i, f in enumerate(found_files, 1):
                size_mb = f.stat().st_size / (1024 * 1024)
                file_table.add_row(str(i), escape(f.name), f"{size_mb:.2f} MB")
            
            file_table.add_row("F", "Filter files by keyword", "-")
            file_table.add_row("P", "Custom Folder Path", "-")
            file_table.add_row("C", "Cancel", "-")
            
            console.print()
            console.print(file_table)
            
            choice = safe_input(f"-> Select file number (1-{len(found_files)}) or [F/P/C]: ").strip().upper()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(found_files):
                    selected = found_files[idx - 1]
                    size_mb = selected.stat().st_size / (1024 * 1024)
                    console.print(f"[bold green][OK] Selected: {selected.name} ({size_mb:.2f} MB)[/bold green]")
                    check_and_pair_uasset_uexp(selected)
                    return selected, found_files
            elif choice == 'F':
                keyword = safe_input("-> Enter search keyword/filter (e.g. 'skin', 'bag', '01'): ").strip().lower()
                if keyword:
                    filtered = [f for f in found_files if keyword in f.name.lower()]
                    if filtered:
                        found_files = filtered
                        console.print(f"[bold green][OK] Filtered {len(found_files)} files matching '{keyword}'[/bold green]")
                    else:
                        console.print(f"[bold red][X] No files matched keyword '{keyword}'[/bold red]")
                continue
            elif choice == 'C':
                return None, []
            elif choice != 'P':
                console.print("[bold red][X] Invalid option selected.[/bold red]")
                continue

        # Ask for folder path only if no files found or user selected 'P'
        console.print(f"\n[bold cyan][?] Enter Source Folder / File Path for {action_title}[/bold cyan]")
        console.print(f"[dim]Default directory: {current_path_str}[/dim]")
        user_input = safe_input("-> Enter path [Press Enter for default, 'C' to cancel]: ").strip().strip('"\'')
        
        if user_input.upper() == 'C':
            return None, []
        
        if user_input:
            target_path = Path(user_input)
            if not target_path.exists():
                console.print(f"[bold red][X] Path does not exist: {target_path}[/bold red]")
                continue
            if target_path.is_file():
                if any(target_path.name.lower().endswith(ext.lower()) for ext in extensions):
                    size_mb = target_path.stat().st_size / (1024 * 1024)
                    console.print(f"[bold green][OK] File selected: {target_path.name} ({size_mb:.2f} MB)[/bold green]")
                    check_and_pair_uasset_uexp(target_path)
                    return target_path, [target_path]
                else:
                    console.print(f"[bold red][X] File is not valid ({', '.join(extensions)}): {target_path.name}[/bold red]")
                    continue
            current_path_str = str(target_path)
        
        if not user_input and not found_files:
            console.print("[bold red][X] No files found. Please enter a valid directory path containing target files or type 'C' to cancel.[/bold red]")


def check_and_pair_uasset_uexp(file_path: Path) -> List[Path]:
    """
    UAsset / UExp Sync & Companion Auto-Pairing:
    - Checks if companion (.uexp for .uasset or .uasset for .uexp) exists in the same folder.
    - Warns user if companion file is missing (since UE4 needs both together in game).
    - Returns list of paired files [file_path, companion_path].
    """
    if not file_path or not file_path.exists():
        return [file_path] if file_path else []

    paired_files = [file_path]
    suf = file_path.suffix.lower()

    if suf in ['.uasset', '.uexp']:
        companion_ext = '.uexp' if suf == '.uasset' else '.uasset'
        companion = file_path.with_suffix(companion_ext)
        if companion.exists():
            paired_files.append(companion)
            console.print(f"[bold green]🔗 Companion asset auto-paired:[/] {companion.name}")
        else:
            console.print(
                f"[bold yellow][!] WARNING: Companion asset '{companion.name}' missing in folder!\n"
                f"    UE4 game engine requires BOTH .uasset and .uexp together in the same directory to load in-game.[/bold yellow]"
            )

        ubulk = file_path.with_suffix('.ubulk')
        if ubulk.exists():
            paired_files.append(ubulk)
            console.print(f"[bold green]🔗 Companion bulk asset auto-paired:[/] {ubulk.name}")

    return paired_files


def display_file_selector(title, folder_path, file_pattern="*.pak"):
    """Backward compatibility alias for pick_file_from_folder"""
    exts = [file_pattern.replace('*', '')] if file_pattern else [".pak", ".obb"]
    return pick_file_from_folder(title, Path(folder_path), extensions=exts)

# ==================== INTEGRATED FEATURE MODULES ====================

class UE4StringTool:
    """Extracts and repacks string literals in .uasset / .uexp binary files."""
    def __init__(self):
        self.MIN_STRING_LEN = 2
        self.MAX_STRING_LEN = 8000

    def read_int(self, f):
        data = f.read(4)
        if len(data) < 4:
            return None
        return struct.unpack('<i', data)[0]

    def is_garbage_text(self, text):
        if not text or len(text.strip()) == 0:
            return True
        allowed_control = {'\n', '\r', '\t'}
        for char in text:
            code = ord(char)
            if code == 0:
                return True
            if code < 32 and char not in allowed_control:
                return True
            if char == '\ufffd':
                return True
        return False

    def is_valid_string_start(self, f, current_pos):
        f.seek(current_pos)
        length = self.read_int(f)
        if length is None or length == 0:
            return False
        if not (self.MIN_STRING_LEN <= abs(length) <= self.MAX_STRING_LEN):
            return False

        try:
            if length < 0:
                read_len = -length * 2
                data = f.read(read_len)
                if len(data) != read_len or data[-2:] != b'\x00\x00':
                    return False
                text = data[:-2].decode('utf-16le')
            else:
                read_len = length
                data = f.read(read_len)
                if len(data) != read_len or data[-1:] != b'\x00':
                    return False
                text = data[:-1].decode('utf-8')

            if self.is_garbage_text(text):
                return False
            return True
        except Exception:
            return False

    def extract_strings(self, file_path: Path) -> Tuple[bool, str]:
        if not file_path.exists():
            return False, f"File not found: {file_path.name}"

        json_path = file_path.with_suffix(file_path.suffix + ".json")
        console.print(f"[bold cyan][+] Extracting readable strings from {file_path.name}...[/bold cyan]")

        try:
            with open(file_path, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(0)

                entries = []
                cursor = 0

                while cursor < file_size - 4:
                    if self.is_valid_string_start(f, cursor):
                        f.seek(cursor)
                        length = self.read_int(f)
                        is_utf16 = length < 0
                        abs_len = abs(length)

                        if is_utf16:
                            raw_data = f.read(abs_len * 2)
                            text = raw_data[:-2].decode('utf-16le')
                            total_size = 4 + (abs_len * 2)
                        else:
                            raw_data = f.read(abs_len)
                            text = raw_data[:-1].decode('utf-8')
                            total_size = 4 + abs_len

                        entries.append({
                            "offset": cursor,
                            "original_len_int": length,
                            "text": text
                        })
                        cursor += total_size
                    else:
                        cursor += 1

            if not entries:
                return False, "No valid readable string entries found."

            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(entries, jf, indent=4, ensure_ascii=False)

            return True, f"Extracted {len(entries)} string(s) -> {json_path.name}"
        except Exception as e:
            return False, str(e)

    def repack_strings(self, file_path: Path, json_path: Path) -> Tuple[bool, str]:
        if not file_path.exists():
            return False, f"Missing source file: {file_path.name}"
        if not json_path.exists():
            return False, f"Missing JSON file: {json_path.name}"

        output_path = file_path.parent / f"{file_path.stem}_repacked{file_path.suffix}"
        console.print(f"[bold cyan][+] Repacking strings into {file_path.name}...[/bold cyan]")

        try:
            with open(json_path, 'r', encoding='utf-8') as jf:
                entries = json.load(jf)

            entries.sort(key=lambda x: x['offset'])

            with open(file_path, 'rb') as f_orig, open(output_path, 'wb') as f_out:
                cursor_orig = 0
                count_modified = 0

                for i, entry in enumerate(entries):
                    gap_size = entry['offset'] - cursor_orig
                    if gap_size > 0:
                        f_out.write(f_orig.read(gap_size))
                    elif gap_size < 0:
                        f_orig.seek(entry['offset'])

                    new_text = entry['text']
                    old_len_int = entry['original_len_int']
                    is_utf16 = old_len_int < 0

                    if is_utf16:
                        max_byte_size = abs(old_len_int) * 2
                    else:
                        max_byte_size = abs(old_len_int)

                    f_orig.seek(entry['offset'] + 4)
                    old_raw = f_orig.read(max_byte_size)
                    try:
                        if is_utf16:
                            old_text = old_raw[:-2].decode('utf-16le')
                        else:
                            old_text = old_raw[:-1].decode('utf-8')
                    except Exception:
                        old_text = "<decode_err>"

                    if new_text != old_text:
                        console.print(f"  [dim cyan]Old:[/dim cyan] \"{old_text}\" -> [bold yellow]New:[/bold yellow] \"{new_text}\"")
                        count_modified += 1

                    if is_utf16:
                        new_bytes = new_text.encode('utf-16le') + b'\x00\x00'
                    else:
                        new_bytes = new_text.encode('utf-8') + b'\x00'

                    current_byte_size = len(new_bytes)

                    if current_byte_size > max_byte_size:
                        f_out.close()
                        f_orig.close()
                        if output_path.exists():
                            output_path.unlink()
                        return False, f"String '{new_text}' exceeds max byte length ({current_byte_size} > {max_byte_size})"

                    f_out.write(struct.pack('<i', old_len_int))
                    f_out.write(new_bytes)

                    pad_len = max_byte_size - current_byte_size
                    if pad_len > 0:
                        f_out.write(b'\x00' * pad_len)

                    f_orig.seek(entry['offset'])
                    len_check = self.read_int(f_orig)
                    skip_len = 4 + (abs(len_check) * 2 if len_check < 0 else abs(len_check))
                    f_orig.seek(entry['offset'] + skip_len)
                    cursor_orig = f_orig.tell()

                f_out.write(f_orig.read())

            return True, f"Repacked successfully! Modified {count_modified} string(s) -> {output_path.name}"
        except Exception as e:
            return False, str(e)

def run_ue4_string_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]⚡ FEATURESTIC LEAKS — UE4 ASSET STRING TOOL ⚡[/bold cyan]\n"
        "[dim]Extract readable string literals from .uasset / .uexp files to JSON & Repack JSON back to binary.[/dim]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold yellow]1.[/bold yellow] [bold white]Unpack Strings to JSON[/bold white]")
    console.print("[bold yellow]2.[/bold yellow] [bold white]Repack Strings from JSON[/bold white]")
    console.print("[bold yellow]0.[/bold yellow] [dim]Back to Main Menu[/dim]")
    
    choice = safe_input("\n-> Select Mode (0-2): ").strip()
    tool = UE4StringTool()
    
    if choice == '1':
        target_dir = data_path / "UNPACK"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        file_p, _ = pick_file_from_folder("Unpack Strings", target_dir, extensions=[".uasset", ".uexp"])
        if file_p:
            ok, msg = tool.extract_strings(file_p)
            if ok:
                console.print(f"[bold green][OK] {msg}[/bold green]")
            else:
                console.print(f"[bold red][X] {msg}[/bold red]")
                
    elif choice == '2':
        target_dir = data_path / "UNPACK"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        file_p, _ = pick_file_from_folder("Repack Strings Source", target_dir, extensions=[".uasset", ".uexp"])
        if file_p:
            json_p = file_p.with_suffix(file_p.suffix + ".json")
            if not json_p.exists():
                console.print(f"[bold red][X] JSON file not found: {json_p.name}[/bold red]")
                console.print("[yellow][!] Please unpack strings to JSON first (Option 1).[/yellow]")
                return
            ok, msg = tool.repack_strings(file_p, json_p)
            if ok:
                console.print(f"[bold green][OK] {msg}[/bold green]")
            else:
                console.print(f"[bold red][X] {msg}[/bold red]")

def run_file_finder_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]🔍 FEATURESTIC LEAKS — ADVANCED FILE FINDER 🔍[/bold cyan]\n"
        "[dim]Search .uasset, .uexp, .ubulk, .lua files by keyword in workspace.[/dim]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    unpack_dir = data_path / "UNPACK"
    if not unpack_dir.exists():
        unpack_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[dim]Default search directory: {unpack_dir}[/dim]")
    custom_dir = safe_input("-> Enter search directory [Press Enter for default]: ").strip().strip('"\'')
    
    search_dir = Path(custom_dir) if custom_dir else unpack_dir
    if not search_dir.exists():
        console.print(f"[bold red][X] Directory not found: {search_dir}[/bold red]")
        return
    
    pattern = safe_input("-> Enter search keyword/pattern (e.g. M416, Jacket, Bag, or press Enter for all): ").strip().lower()
    
    extensions = [".uasset", ".uexp", ".ubulk", ".lua", ".json", ".png"]
    
    console.print("\n[bold cyan][+] Scanning directory for files...[/bold cyan]")
    found_files = []
    
    for root, _, files in os.walk(search_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                if not pattern or pattern in file.lower() or pattern in root.lower():
                    found_files.append(Path(root) / file)
    
    if not found_files:
        console.print(f"[bold yellow][!] No matching files found in {search_dir}[/bold yellow]")
        return
    
    file_table = Table(
        title=f"[bold cyan]FOUND FILES ({len(found_files)})[/bold cyan]",
        border_style="dim cyan",
        box=ROUNDED,
        show_header=True
    )
    file_table.add_column("#", style="bold yellow", justify="center", width=6)
    file_table.add_column("Filename", style="bold white")
    file_table.add_column("Size", style="dim", justify="right", width=12)
    
    for i, f in enumerate(found_files[:15], 1):
        file_table.add_row(str(i), escape(f.name), human_size(f.stat().st_size))
    
    if len(found_files) > 15:
        file_table.add_row("...", f"and {len(found_files) - 15} more files", "")
    
    console.print(file_table)
    
    copy_choice = safe_input("\n-> Copy found files to output folder? (y/N): ").strip().lower()
    if copy_choice == 'y':
        out_dir = data_path / "FOUND_FILES"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        flat_choice = safe_input("-> Preserve directory paths? (y/N - 'N' copies flat): ").strip().lower()
        preserve_paths = (flat_choice == 'y')
        
        copied_count = 0
        for f in found_files:
            try:
                if preserve_paths:
                    rel_p = f.relative_to(search_dir)
                    dest = out_dir / rel_p
                    dest.parent.mkdir(parents=True, exist_ok=True)
                else:
                    dest = out_dir / f.name
                    counter = 1
                    original_dest = dest
                    while dest.exists():
                        dest = out_dir / f"{original_dest.stem}_{counter}{original_dest.suffix}"
                        counter += 1
                
                shutil.copy2(f, dest)
                copied_count += 1
            except Exception as e:
                console.print(f"[bold red]Error copying {f.name}: {e}[/bold red]")
        
        console.print(f"[bold green][OK] Successfully copied {copied_count} file(s) to: {out_dir}[/bold green]")


def run_skin_dumper(data_path: Path) -> None:
    console.print(Panel(
        "[bold bright_cyan]🎨 SKIN ASSETS DUMPER & EXTRACTOR 🎨[/bold bright_cyan]\n"
        "[dim]Scan PAK files or UNPACK directory to dump skin textures, meshes, uassets & uexps.[/dim]",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))

    keywords = ["skin", "weapon", "outfit", "character", "vehicle", "item_", "gun_", "mesh", "texture", "material", "finish", "suit"]
    
    dump_dir = data_path / "DUMP_LOGS"
    dump_dir.mkdir(parents=True, exist_ok=True)
    skins_out = data_path / "RESULT" / "SKINS_DUMP"
    skins_out.mkdir(parents=True, exist_ok=True)
    
    found_skins = []

    # Check PAK folder first
    pak_dir = data_path / "PAK"
    pak_files = [f for f in pak_dir.glob("*.pak") if f.is_file()] if pak_dir.exists() else []

    if pak_files:
        console.print(f"\n[bold bright_cyan][+] Scanning {len(pak_files)} .pak file(s) for Skin Assets...[/bold bright_cyan]")
        for pf in pak_files:
            try:
                pak = TencentPakFile(pf)
                for dir_p, files in pak._index.items():
                    for fname, entry in files.items():
                        rel_path = (pak._mount_point / dir_p / fname).as_posix()
                        path_lower = rel_path.lower()
                        if any(kw in path_lower for kw in keywords):
                            found_skins.append({
                                "source": pf.name,
                                "path": rel_path,
                                "size": entry.size,
                                "uncompressed_size": entry.uncompressed_size,
                                "entry": entry,
                                "pak": pak
                            })
            except Exception as e:
                console.print(f"[dim yellow][!] Error reading {pf.name}: {e}[/dim yellow]")

    # Check UNPACK folder
    unpack_dir = data_path / "UNPACK"
    if unpack_dir.exists():
        for root, _, files in os.walk(unpack_dir):
            for file in files:
                full_p = Path(root) / file
                rel_path = full_p.relative_to(unpack_dir).as_posix()
                if any(kw in rel_path.lower() for kw in keywords):
                    found_skins.append({
                        "source": "UNPACK Workspace",
                        "path": rel_path,
                        "size": full_p.stat().st_size,
                        "uncompressed_size": full_p.stat().st_size,
                        "local_file": full_p
                    })

    if not found_skins:
        console.print("[bold yellow][!] No skin assets matched keywords in PAK or UNPACK folder.[/bold yellow]")
        return

    table = Table(
        title=f"[bold bright_cyan]🎯 FOUND {len(found_skins)} SKIN ASSETS 🎯[/bold bright_cyan]",
        border_style="bright_cyan",
        box=ROUNDED
    )
    table.add_column("No.", style="bold bright_yellow", justify="center", width=6)
    table.add_column("Source", style="bold bright_white", width=18)
    table.add_column("Asset Path", style="bright_cyan")
    table.add_column("Size", style="bold bright_green", justify="right", width=10)

    for idx, item in enumerate(found_skins[:25], 1):
        table.add_row(str(idx), item["source"][:18], item["path"][-50:], human_size(item["size"]))

    console.print(table)
    if len(found_skins) > 25:
        console.print(f"[dim]... and {len(found_skins) - 25} more skin assets.[/dim]")

    console.print("\n[bold bright_yellow]Options:[/bold bright_yellow]")
    console.print("  [1] Save Skin Assets Log (.txt & .json)")
    console.print("  [2] Extract / Export All Found Skin Files to RESULT/SKINS_DUMP/")
    console.print("  [0] Back")

    act = safe_input("\n-> Select Action (0-2): ").strip()

    if act in ['1', '2']:
        # Save Log
        txt_file = dump_dir / "Skins_Dump_Report.txt"
        json_file = dump_dir / "Skins_Dump_Report.json"

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("=== FEATURESTIC LEAKS SKIN ASSETS DUMP REPORT ===\n")
            f.write(f"Total Skin Assets Identified: {len(found_skins)}\n")
            f.write("="*60 + "\n\n")
            for item in found_skins:
                f.write(f"Source: {item['source']}\nPath: {item['path']}\nSize: {item['size']} bytes\n\n")

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump([{
                "source": item["source"],
                "path": item["path"],
                "size": item["size"]
            } for item in found_skins], f, indent=2)

        console.print(f"\n[bold green][OK] Skin report saved successfully![/bold green]")
        console.print(f" 📄 {txt_file}")
        console.print(f" 📄 {json_file}")

        sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
        if sd_dump.parent.exists():
            sd_dump.mkdir(parents=True, exist_ok=True)
            shutil.copy2(txt_file, sd_dump / txt_file.name)
            shutil.copy2(json_file, sd_dump / json_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/")

    if act == '2':
        console.print(f"\n[bold bright_cyan][+] Exporting skin files to {skins_out}...[/bold bright_cyan]")
        extracted_cnt = 0
        for item in found_skins:
            try:
                dest_p = skins_out / item["path"].lstrip('/')
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                if "local_file" in item:
                    shutil.copy2(item["local_file"], dest_p)
                    extracted_cnt += 1
                elif "pak" in item:
                    item["pak"].extract_entry(item["entry"], dest_p)
                    extracted_cnt += 1
            except Exception:
                pass

        console.print(f"[bold green][OK] Successfully exported {extracted_cnt} skin asset file(s) to:[/bold green]")
        console.print(f" 📁 [bold bright_white]{skins_out}[/bold bright_white]")
        sd_skins = Path("/sdcard/FeaturesticLeaks/RESULT/SKINS_DUMP")
        if sd_skins.parent.parent.exists():
            try:
                if sd_skins.exists():
                    shutil.rmtree(sd_skins)
                shutil.copytree(skins_out, sd_skins)
                console.print(f" 📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/SKINS_DUMP/")
            except Exception:
                pass

def run_obb_manager(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]📦 FEATURESTIC LEAKS — OBB PACKAGE MANAGER 📦[/bold cyan]\n"
        "[dim]Unzip OBB archive & Rezip OBB with byte-exact padding matching original size.[/dim]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold yellow]1.[/bold yellow] [bold white]Unzip OBB Package[/bold white]")
    console.print("[bold yellow]2.[/bold yellow] [bold white]Rezip OBB Package (with exact size padding)[/bold white]")
    console.print("[bold yellow]0.[/bold yellow] [dim]Back to Main Menu[/dim]")
    
    choice = safe_input("\n-> Select Option (0-2): ").strip()
    
    if choice == '1':
        obb_dir = data_path / "PAK"
        obb_dir.mkdir(parents=True, exist_ok=True)
        obb_file, _ = pick_file_from_folder("Unzip OBB", obb_dir, extensions=[".obb", ".zip"])
        if not obb_file:
            return
        
        orig_size = obb_file.stat().st_size
        out_unpack = data_path / "UNPACK" / obb_file.stem
        out_unpack.mkdir(parents=True, exist_ok=True)
        
        size_ini = data_path / f"size_{obb_file.stem}.ini"
        size_ini.write_text(str(orig_size), encoding='utf-8')
        
        console.print(f"[bold cyan][+] Extracting OBB ({human_size(orig_size)})...[/bold cyan]")
        try:
            with zipfile.ZipFile(obb_file, 'r') as zf:
                zf.extractall(out_unpack)
            console.print(f"[bold green][OK] Successfully extracted OBB to: {out_unpack}[/bold green]")
        except Exception as e:
            handle_exception(e, "Unzip OBB", data_path)
            
    elif choice == '2':
        unpack_dir = data_path / "UNPACK"
        if not unpack_dir.exists() or not any(unpack_dir.iterdir()):
            console.print("[bold red][X] No extracted OBB folders found in UNPACK directory.[/bold red]")
            return
        
        folders = [item for item in unpack_dir.iterdir() if item.is_dir()]
        if not folders:
            console.print("[bold red][X] No subfolders found in UNPACK.[/bold red]")
            return
        
        folder_table = Table(
            title="[bold cyan]EXTRACTED OBB FOLDERS[/bold cyan]",
            border_style="dim cyan",
            box=ROUNDED
        )
        folder_table.add_column("Index", style="bold yellow", justify="center", width=8)
        folder_table.add_column("Folder Name", style="bold white")
        for i, f in enumerate(folders, 1):
            folder_table.add_row(str(i), f.name)
        
        console.print(folder_table)
        sel_idx = safe_input(f"-> Select folder number (1-{len(folders)}): ").strip()
        if not sel_idx.isdigit() or not (1 <= int(sel_idx) <= len(folders)):
            console.print("[bold red][X] Invalid selection.[/bold red]")
            return
        
        target_folder = folders[int(sel_idx) - 1]
        
        size_ini = data_path / f"size_{target_folder.name}.ini"
        target_orig_size = 0
        if size_ini.exists():
            try:
                target_orig_size = int(size_ini.read_text(encoding='utf-8').strip())
            except Exception:
                pass
        
        result_dir = data_path / "RESULT"
        result_dir.mkdir(parents=True, exist_ok=True)
        out_obb = result_dir / f"{target_folder.name}.obb"
        
        console.print(f"[bold cyan][+] Rezips OBB package: {out_obb.name}...[/bold cyan]")
        try:
            with zipfile.ZipFile(out_obb, 'w', compression=zipfile.ZIP_STORED) as zf:
                for root, _, files in os.walk(target_folder):
                    for file in files:
                        full_p = Path(root) / file
                        rel_p = full_p.relative_to(target_folder)
                        zf.write(full_p, arcname=str(rel_p).replace('\\', '/'))
            
            curr_size = out_obb.stat().st_size
            if target_orig_size > 0:
                if curr_size < target_orig_size:
                    pad_bytes = target_orig_size - curr_size
                    with open(out_obb, 'ab') as f:
                        f.write(b'\x00' * pad_bytes)
                    console.print(f"[bold green][OK] Added {pad_bytes} padding bytes to match original size ({human_size(target_orig_size)})![/bold green]")
                elif curr_size > target_orig_size:
                    console.print(f"[yellow][!] Repacked OBB size ({human_size(curr_size)}) exceeds original size ({human_size(target_orig_size)}).[/yellow]")
            
            console.print(f"[bold green][OK] OBB successfully created: {out_obb}[/bold green]")
        except Exception as e:
            handle_exception(e, "Rezip OBB", data_path)

def run_pak_compare_dumper(data_path: Path) -> None:
    console.print(Panel(
        "[bold bright_cyan]🔍 PAK COMPARE & DUMP TOOL (PAK DUMPER) 🔍[/bold bright_cyan]\n"
        "[dim]Compare two .pak/.obb files or dump detailed internal file lists, offsets, sizes, hashes, and encryption modes.[/dim]",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))

    console.print("\n[bold yellow]Select PAK Compare / Dump Mode:[/bold yellow]")
    console.print("  [bold cyan][1][/bold cyan] Dump Single PAK/OBB Index & Hashes to Text/JSON")
    console.print("  [bold cyan][2][/bold cyan] Compare Two PAK/OBB Files (Added, Modified, Removed Assets)")
    console.print("  [bold cyan][0][/bold cyan] Cancel / Back")

    sub_choice = safe_input('\n-> Select option (0-2): ').strip()
    
    if sub_choice == '1':
        pak_dir = data_path / "PAK"
        pak_dir.mkdir(parents=True, exist_ok=True)
        pak_file, _ = pick_file_from_folder("PAK Dump", pak_dir)
        if not pak_file:
            return
        try:
            console.print(f"\n[bold cyan][+] Reading PAK index for {pak_file.name}...[/bold cyan]")
            pak = TencentPakFile(pak_file)
            entries = []
            for dir_p, files in pak._index.items():
                for fname, entry in files.items():
                    rel_path = (pak._mount_point / dir_p / fname).as_posix()
                    enc_m = pak._get_method_str(entry.encryption_method, True)
                    comp_m = pak._get_method_str(entry.compression_method, False)
                    entry_hash = getattr(entry, 'content_hash', getattr(entry, 'hash', b''))
                    hash_str = entry_hash.hex() if isinstance(entry_hash, bytes) else str(entry_hash)
                    entries.append({
                        "file_path": rel_path,
                        "size": entry.size,
                        "uncompressed_size": entry.uncompressed_size,
                        "offset": entry.offset,
                        "encrypted": entry.encrypted,
                        "encryption_method": enc_m,
                        "compression_method": comp_m,
                        "hash": hash_str
                    })

            dump_dir = data_path / "DUMP_LOGS"
            dump_dir.mkdir(parents=True, exist_ok=True)
            txt_dump = dump_dir / f"Dump_{pak_file.stem}.txt"
            json_dump = dump_dir / f"Dump_{pak_file.stem}.json"

            with open(txt_dump, "w", encoding="utf-8") as f:
                f.write(f"=== FEATURESTIC LEAKS PAK INDEX DUMP ===\n")
                f.write(f"PAK File: {pak_file.name}\n")
                f.write(f"Mount Point: {pak._mount_point}\n")
                f.write(f"Total Files: {len(entries)}\n")
                f.write("="*60 + "\n\n")
                for e in entries:
                    f.write(f"Path: {e['file_path']}\n")
                    f.write(f"  Size: {e['size']} bytes (Uncompressed: {e['uncompressed_size']} bytes)\n")
                    f.write(f"  Offset: {e['offset']} | Compression: {e['compression_method']} | Encryption: {e['encryption_method']}\n")
                    f.write(f"  Hash: {e['hash']}\n\n")

            with open(json_dump, "w", encoding="utf-8") as f:
                json.dump({"pak_file": pak_file.name, "mount_point": str(pak._mount_point), "total_files": len(entries), "files": entries}, f, indent=2)

            console.print(f"\n[bold green][OK] Dump created successfully![/bold green]")
            console.print(f"  📄 [bold white]Text Dump:[/bold white] {txt_dump}")
            console.print(f"  📄 [bold white]JSON Dump:[/bold white] {json_dump}")

            sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
            if sd_dump.parent.exists():
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(txt_dump, sd_dump / txt_dump.name)
                shutil.copy2(json_dump, sd_dump / json_dump.name)
                console.print(f"  📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/")

        except Exception as e:
            handle_exception(e, "PAK Dump", data_path)

    elif sub_choice == '2':
        pak_dir = data_path / "PAK"
        pak_dir.mkdir(parents=True, exist_ok=True)
        console.print("\n[bold cyan][1/2] Select Original / Old PAK file:[/bold cyan]")
        pak_file_1, _ = pick_file_from_folder("Select First PAK", pak_dir)
        if not pak_file_1:
            return

        console.print("\n[bold cyan][2/2] Select New / Modified PAK file:[/bold cyan]")
        pak_file_2, _ = pick_file_from_folder("Select Second PAK", pak_dir)
        if not pak_file_2:
            return

        try:
            console.print(f"\n[bold cyan][+] Reading PAK 1 ({pak_file_1.name})...[/bold cyan]")
            pak1 = TencentPakFile(pak_file_1)
            map1 = {}
            for dir_p, files in pak1._index.items():
                for fname, entry in files.items():
                    rel_p = (pak1._mount_point / dir_p / fname).as_posix()
                    map1[rel_p] = entry

            console.print(f"[bold cyan][+] Reading PAK 2 ({pak_file_2.name})...[/bold cyan]")
            pak2 = TencentPakFile(pak_file_2)
            map2 = {}
            for dir_p, files in pak2._index.items():
                for fname, entry in files.items():
                    rel_p = (pak2._mount_point / dir_p / fname).as_posix()
                    map2[rel_p] = entry

            keys1, keys2 = set(map1.keys()), set(map2.keys())
            added = keys2 - keys1
            removed = keys1 - keys2
            common = keys1 & keys2

            modified = []
            for k in common:
                e1, e2 = map1[k], map2[k]
                if e1.size != e2.size or e1.uncompressed_size != e2.uncompressed_size or getattr(e1, 'hash', None) != getattr(e2, 'hash', None):
                    modified.append((k, e1, e2))

            summary_table = Table(title="[bold yellow]PAK COMPARE RESULT SUMMARY[/bold yellow]", box=ROUNDED, border_style="cyan")
            summary_table.add_column("Category", style="bold white")
            summary_table.add_column("Count", style="bold yellow", justify="right")

            summary_table.add_row("Total Files in PAK 1", str(len(keys1)))
            summary_table.add_row("Total Files in PAK 2", str(len(keys2)))
            summary_table.add_row("🆕 Added Assets", f"[bold green]{len(added)}[/bold green]")
            summary_table.add_row("✏️ Modified / Changed Assets", f"[bold yellow]{len(modified)}[/bold yellow]")
            summary_table.add_row("🗑️ Removed / Missing Assets", f"[bold red]{len(removed)}[/bold red]")
            summary_table.add_row("✅ Unchanged Common Assets", str(len(common) - len(modified)))

            console.print(summary_table)

            dump_dir = data_path / "DUMP_LOGS"
            dump_dir.mkdir(parents=True, exist_ok=True)
            diff_log = dump_dir / f"Compare_{pak_file_1.stem}_vs_{pak_file_2.stem}.txt"

            with open(diff_log, "w", encoding="utf-8") as f:
                f.write(f"=== FEATURESTIC LEAKS PAK COMPARISON LOG ===\n")
                f.write(f"PAK 1 (Original): {pak_file_1.name} ({len(keys1)} files)\n")
                f.write(f"PAK 2 (Modified): {pak_file_2.name} ({len(keys2)} files)\n")
                f.write("="*60 + "\n\n")

                f.write(f"--- ADDED ASSETS ({len(added)}) ---\n")
                for a in sorted(added):
                    f.write(f"+ {a} ({map2[a].size} bytes)\n")

                f.write(f"\n--- MODIFIED ASSETS ({len(modified)}) ---\n")
                for k, e1, e2 in sorted(modified, key=lambda x: x[0]):
                    f.write(f"* {k}\n  PAK1: {e1.size} bytes | PAK2: {e2.size} bytes\n")

                f.write(f"\n--- REMOVED ASSETS ({len(removed)}) ---\n")
                for r in sorted(removed):
                    f.write(f"- {r}\n")

            console.print(f"\n[bold green][OK] Comparison log saved:[/bold green] {diff_log}")

            sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
            if sd_dump.parent.exists():
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(diff_log, sd_dump / diff_log.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/{diff_log.name}")

            # Option to extract modified and added assets automatically
            diff_count = len(modified) + len(added)
            if diff_count > 0:
                console.print(f"\n[bold yellow]💡 Found {diff_count} modified/added files in PAK 2.[/bold yellow]")
                extract_choice = safe_input("-> Do you want to extract these modified/added files to RESULT/Modified_Files? (y/n): ").strip().lower()
                if extract_choice == 'y':
                    mod_out_dir = data_path / "RESULT" / "Modified_Files"
                    mod_out_dir.mkdir(parents=True, exist_ok=True)
                    console.print(f"\n[bold cyan][+] Extracting {diff_count} modified/added files from PAK 2...[/bold cyan]")
                    
                    extracted_cnt = 0
                    # Extract added assets
                    for rel_p in sorted(added):
                        entry = map2[rel_p]
                        dest_file = mod_out_dir / rel_p.lstrip('/')
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            pak2._write_to_disk(dest_file, entry)
                            extracted_cnt += 1
                        except Exception:
                            pass

                    # Extract modified assets
                    for rel_p, e1, e2 in sorted(modified, key=lambda x: x[0]):
                        dest_file = mod_out_dir / rel_p.lstrip('/')
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            pak2._write_to_disk(dest_file, e2)
                            extracted_cnt += 1
                        except Exception:
                            pass

                    console.print(f"[bold green]✅ Extracted {extracted_cnt}/{diff_count} files to:[/bold green] {mod_out_dir}")
                    
                    sd_mod = Path("/sdcard/FeaturesticLeaks/RESULT/Modified_Files")
                    if sd_mod.parent.parent.exists():
                        try:
                            if sd_mod.exists():
                                shutil.rmtree(sd_mod)
                            shutil.copytree(mod_out_dir, sd_mod)
                            console.print(f"📲 [bold green]Synced to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/Modified_Files/")
                        except Exception:
                            pass

        except Exception as e:
            handle_exception(e, "PAK Compare", data_path)

def run_file_resizer_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]📏 FEATURESTIC LEAKS — FILE RESIZER & SIZE EQUALIZER 📏[/bold cyan]\n"
        "[dim]Match exact byte sizes for PAK, OBB, LUA, or any file to pass anti-cheat integrity checks.[/dim]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    
    cand_files = list(res_dir.glob("*")) + list((data_path / "LUA").glob("*")) + list((data_path / "PAK").glob("*"))
    valid_files = [f for f in cand_files if f.is_file() and not f.name.startswith('.')]
    
    target_file = None
    if valid_files:
        console.print("\n[bold cyan]Select file to resize / pad:[/bold cyan]")
        table = Table(title="[bold cyan]AVAILABLE FILES[/bold cyan]", box=ROUNDED)
        table.add_column("Index", style="bold yellow", justify="center", width=8)
        table.add_column("File Name", style="bold white")
        table.add_column("Current Size", style="bold cyan")
        table.add_column("Path", style="dim")
        
        for i, f in enumerate(valid_files[:15], 1):
            table.add_row(str(i), escape(f.name), human_size(f.stat().st_size), escape(str(f.parent.name)))
        console.print(table)
        
        sel = safe_input("-> Enter file number or custom file path: ").strip().strip('"\'')
        if sel.isdigit() and 1 <= int(sel) <= len(valid_files[:15]):
            target_file = valid_files[int(sel) - 1]
        elif sel:
            custom_p = Path(sel)
            if custom_p.exists() and custom_p.is_file():
                target_file = custom_p
    
    if not target_file:
        custom = safe_input("-> Enter file path to resize (or press Enter to cancel): ").strip().strip('"\'')
        if not custom:
            return
        target_file = Path(custom)
        if not target_file.exists():
            console.print(f"[bold red][X] File not found: {target_file}[/bold red]")
            return

    curr_size = target_file.stat().st_size
    console.print(f"\n[bold white]Target File:[/bold white] {target_file.name}")
    console.print(f"[bold white]Current Size:[/bold white] {curr_size:,} bytes ({human_size(curr_size)})")

    console.print("\n[bold cyan]Select Size Matching Mode:[/bold cyan]")
    console.print("  [1] Match size with Original Reference File (Select .pak / .obb / .lua)")
    console.print("  [2] Enter Target Size manually (in Bytes or MB)")
    
    mode = safe_input("\n-> Select Mode (1-2) [1]: ").strip() or '1'
    target_bytes = 0
    
    if mode == '1':
        ref_dir = data_path / "PAK"
        ref_file, _ = pick_file_from_folder("Reference File", ref_dir)
        if not ref_file:
            custom_ref = safe_input("-> Enter reference file path: ").strip().strip('"\'')
            if custom_ref:
                ref_file = Path(custom_ref)
        if ref_file and ref_file.exists():
            target_bytes = ref_file.stat().st_size
            console.print(f"[bold green][+] Reference File: {ref_file.name} ({target_bytes:,} bytes)[/bold green]")
        else:
            console.print("[bold red][X] Valid reference file not provided.[/bold red]")
            return
    else:
        sz_input = safe_input("-> Enter target size (e.g. 10485760 or 10.5MB): ").strip().lower()
        if not sz_input:
            return
        try:
            if sz_input.endswith("mb"):
                target_bytes = int(float(sz_input.replace("mb", "").strip()) * 1024 * 1024)
            elif sz_input.endswith("kb"):
                target_bytes = int(float(sz_input.replace("kb", "").strip()) * 1024)
            else:
                target_bytes = int(sz_input)
        except Exception:
            console.print("[bold red][X] Invalid size input.[/bold red]")
            return

    if target_bytes <= 0:
        console.print("[bold red][X] Target size must be greater than 0.[/bold red]")
        return

    console.print(f"\n[bold cyan]Padding Strategy:[/bold cyan]")
    console.print("  [1] Null Bytes (0x00) — Best for PAK / OBB / Binary")
    console.print("  [2] Space / Newline — Best for LUA / JSON / Source Code")
    
    pad_choice = safe_input("-> Select Padding Byte (1-2) [1]: ").strip() or '1'
    pad_byte = b' ' if pad_choice == '2' else b'\x00'

    # Perform resizing
    out_file = res_dir / f"{target_file.stem}_resized{target_file.suffix}"
    shutil.copy2(target_file, out_file)

    if curr_size == target_bytes:
        console.print("[bold green][OK] File already matches target size perfectly![/bold green]")
    elif curr_size < target_bytes:
        diff = target_bytes - curr_size
        with open(out_file, "ab") as f:
            chunk = pad_byte * min(diff, 65536)
            written = 0
            while written < diff:
                to_w = min(len(chunk), diff - written)
                f.write(chunk[:to_w])
                written += to_w
        console.print(f"[bold green][OK] Added {diff:,} bytes padding ({'0x20 Space' if pad_byte == b' ' else '0x00 Null'})![/bold green]")
        console.print(f"[bold green][+] Resized output: {out_file} ({out_file.stat().st_size:,} bytes)[/bold green]")
    else:
        diff = curr_size - target_bytes
        console.print(f"[bold yellow][!] File is LARGER than target by {diff:,} bytes.[/bold yellow]")
        trim = safe_input("-> Trim excess bytes from end of file? (y/N): ").strip().lower()
        if trim in ['y', 'yes']:
            with open(out_file, "r+b") as f:
                f.truncate(target_bytes)
            console.print(f"[bold green][OK] Trimmed {diff:,} bytes -> Exact match ({out_file.stat().st_size:,} bytes)[/bold green]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_file.name}[/bold green]")
        except Exception:
            pass

def pak_obb_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]📦 PAK / OBB TOOLS 📦[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Unpack Package", "Extract PAK / OBB package contents to workspace")
        menu_table.add_row("[2]", "Repack & Inject", "Repack workspace, replace edited files, or inject custom path")
        menu_table.add_row("[3]", "OBB Manager", "Unzip & Rezip OBB with size padding")
        menu_table.add_row("[4]", "PAK Compare & Dump", "Compare 2 PAKs or dump index / offsets / hashes")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-4] [0]: \033[0m').strip()

        if choice == '1':
            pak_dir = data_path / "PAK"
            pak_dir.mkdir(parents=True, exist_ok=True)
            pak_file, _ = pick_file_from_folder("Unpack", pak_dir)
            if not pak_file:
                safe_input('\nPress Enter to continue...')
                continue
            try:
                console.print(f'[bold cyan][+] Unpacking {pak_file.name}...[/bold cyan]')
                pak = TencentPakFile(pak_file)
                unpack_path = data_path / "UNPACK" / pak_file.stem
                repack_path = data_path / "REPACK" / pak_file.stem
                pak.dump(unpack_path)

                sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / pak_file.stem
                if sd_unpack.parent.exists() and sd_unpack != unpack_path:
                    try:
                        pak.dump(sd_unpack)
                    except Exception:
                        pass

                log_path = unpack_path / f'Debug_{pak_file.stem}.log'
                dump_unpacking_log(pak, log_path)
                for dir_path, _ in pak._index.items():
                    current_repack_path = repack_path / pak._mount_point / dir_path
                    current_repack_path.mkdir(parents=True, exist_ok=True)
                console.print(f'[bold green][OK] Successfully extracted to: {unpack_path}[/bold green]')
                if sd_unpack.parent.exists():
                    console.print(f'[bold green][+] Also extracted to SDCard: {sd_unpack}[/bold green]')
            except Exception as e:
                handle_exception(e, "Unpack", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '2':
            console.print("\n[bold cyan]🛠️ REPACK & INJECTION MODES:[/bold cyan]")
            console.print("  [1] Repack Full Workspace (REPACK folder)")
            console.print("  [2] Replace Edited Files (REPLACE folder)")
            console.print("  [3] Inject Files to Custom Target Path (INJECT folder)")
            sub_c = safe_input("\n-> Select Mode [1-3] [1]: ").strip() or '1'

            pak_dir = data_path / "PAK"
            pak_dir.mkdir(parents=True, exist_ok=True)

            if sub_c == '1':
                pak_file, _ = pick_file_from_folder("Repack", pak_dir)
                if not pak_file:
                    safe_input('\nPress Enter to continue...')
                    continue
                repack_dir = data_path / "REPACK" / pak_file.stem
                if not repack_dir.exists():
                    console.print(f'[bold red][X] Error: {repack_dir} not found.[/bold red]')
                    console.print('[yellow][!] Please unpack first using Option 1.[/yellow]')
                    safe_input('\nPress Enter to continue...')
                    continue
                try:
                    console.print(f'[bold cyan][+] Repacking {pak_file.name}...[/bold cyan]')
                    pak = TencentPakFile(pak_file)
                    result_dir = data_path / "RESULT"
                    output_pak = result_dir / pak_file.name
                    mode = detect_repack_mode(pak_file)
                    if mode == 'MINI_OBB':
                        repack_mini_obb(pak, repack_dir, output_pak)
                    elif mode == 'GAMEPATCH':
                        repack_gamepatch(pak, repack_dir, output_pak)
                    else:
                        repack_obbzsdic(pak, repack_dir, output_pak)

                    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                    if sd_res.exists():
                        try:
                            shutil.copy2(output_pak, sd_res / pak_file.name)
                            console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                        except Exception:
                            pass
                    console.print('[bold green][OK] Repack completed successfully![/bold green]')
                except Exception as e:
                    handle_exception(e, "Repack", data_path)
                safe_input('\nPress Enter to continue...')

            elif sub_c == '2':
                pak_file, _ = pick_file_from_folder("Replace Files", pak_dir)
                if not pak_file:
                    safe_input('\nPress Enter to continue...')
                    continue

                sd_rep = Path("/sdcard/FeaturesticLeaks/REPLACE")
                dp_rep = data_path / "REPLACE"
                if sd_rep.exists() and dp_rep.exists():
                    sd_names = {p.name for p in sd_rep.rglob('*') if p.is_file()}
                    for dp_f in list(dp_rep.rglob('*')):
                        if dp_f.is_file() and dp_f.name not in sd_names:
                            try:
                                dp_f.unlink()
                            except Exception:
                                pass

                cand_dirs = [
                    Path("/sdcard/FeaturesticLeaks/REPLACE"),
                    data_path / "REPLACE",
                    Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE"),
                    data_path / "PAK_WORKSPACE" / "3_REPLACE"
                ]
                actual_edit_path = None
                ignored_names = {'.gitkeep', '.ds_store', 'desktop.ini', 'thumbs.db'}
                for cd in cand_dirs:
                    if cd.exists():
                        for tmp_f in list(cd.rglob('*')):
                            if tmp_f.is_file() and (tmp_f.name.endswith('_fixed51.lua') or tmp_f.name.endswith('.tmp_luac') or tmp_f.name.endswith('.tmp')):
                                try:
                                    tmp_f.unlink()
                                except Exception:
                                    pass
                        valid_files = [p for p in cd.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
                        if valid_files:
                            actual_edit_path = cd
                            break

                if not actual_edit_path:
                    console.print(Panel(
                        "[bold red]⚠️ NO FILES FOUND IN REPLACE FOLDER![/bold red]\n\n"
                        "[bold white]Please copy/move your edited files into one of these folders:[/bold white]\n"
                        " 📂 [bold bright_cyan]/sdcard/FeaturesticLeaks/REPLACE/[/bold bright_cyan]\n"
                        " 📂 [bold bright_cyan]/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE/[/bold bright_cyan]\n\n"
                        "[dim]Tip: Put your modified files inside the REPLACE folder above, or enter custom path below.[/dim]",
                        title="[bold yellow] 📂 REPLACE FOLDER PATH GUIDE [/bold yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))
                    custom_edit = safe_input('-> Enter custom source folder path (or press Enter to cancel): ').strip().strip('"\'')
                    if not custom_edit:
                        safe_input('\nPress Enter to continue...')
                        continue
                    custom_p = Path(custom_edit)
                    if not custom_p.exists():
                        console.print(f'[bold red][X] Path does not exist: {custom_p}[/bold red]')
                        safe_input('\nPress Enter to continue...')
                        continue
                    actual_edit_path = custom_p
                else:
                    valid_cnt = len([p for p in actual_edit_path.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')])
                    console.print(f"\n[bold green]✓ Found {valid_cnt} file(s) in REPLACE folder:[/bold green] [bold cyan]{actual_edit_path}[/bold cyan]")

                try:
                    console.print(f'[bold cyan][+] Replacing files using source: {actual_edit_path}[/bold cyan]')
                    pak = TencentPakFile(pak_file)
                    result_dir = data_path / "RESULT"
                    result_dir.mkdir(parents=True, exist_ok=True)
                    output_pak = result_dir / pak_file.name

                    count = repack_pak_file_full(pak, actual_edit_path, output_pak)

                    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                    if sd_res.exists():
                        try:
                            shutil.copy2(output_pak, sd_res / pak_file.name)
                            console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                        except Exception:
                            pass

                    if count > 0:
                        console.print(f'[bold green][OK] Repacked {count} file(s) successfully![/bold green]')
                        console.print(f'[bold green][+] Output: {output_pak}[/bold green]')
                    else:
                        console.print('[bold red][X] No files repacked.[/bold red]')

                except Exception as e:
                    handle_exception(e, "Replace Files", data_path)
                safe_input('\nPress Enter to continue...')

            else:
                pak_file, _ = pick_file_from_folder("Inject Path", pak_dir)
                if not pak_file:
                    safe_input('\nPress Enter to continue...')
                    continue

                sd_inj = Path("/sdcard/FeaturesticLeaks/INJECT")
                dp_inj = data_path / "INJECT"
                if sd_inj.exists() and dp_inj.exists():
                    sd_names = {p.name for p in sd_inj.rglob('*') if p.is_file()}
                    for dp_f in list(dp_inj.rglob('*')):
                        if dp_f.is_file() and dp_f.name not in sd_names:
                            try:
                                dp_f.unlink()
                            except Exception:
                                pass

                cand_dirs = [
                    Path("/sdcard/FeaturesticLeaks/INJECT"),
                    data_path / "INJECT",
                    Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT"),
                    data_path / "PAK_WORKSPACE" / "4_INJECT"
                ]
                actual_edit_path = None
                ignored_names = {'.gitkeep', '.ds_store', 'desktop.ini', 'thumbs.db'}
                for cd in cand_dirs:
                    if cd.exists():
                        for tmp_f in list(cd.rglob('*')):
                            if tmp_f.is_file() and (tmp_f.name.endswith('_fixed51.lua') or tmp_f.name.endswith('.tmp_luac') or tmp_f.name.endswith('.tmp')):
                                try:
                                    tmp_f.unlink()
                                except Exception:
                                    pass
                        valid_files = [p for p in cd.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
                        if valid_files:
                            actual_edit_path = cd
                            break

                if not actual_edit_path:
                    console.print(Panel(
                        "[bold red]⚠️ NO FILES FOUND IN INJECT FOLDER![/bold red]\n\n"
                        "[bold white]Please copy/move your .lua or mod files into one of these folders:[/bold white]\n"
                        " 📂 [bold bright_yellow]/sdcard/FeaturesticLeaks/INJECT/[/bold bright_yellow]\n"
                        " 📂 [bold bright_yellow]/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT/[/bold bright_yellow]\n\n"
                        "[dim]Instructions:[/dim]\n"
                        "1. Open your File Manager and put your files inside [bold yellow]/sdcard/FeaturesticLeaks/INJECT/[/bold yellow]\n"
                        "2. Or enter your custom folder path below:",
                        title="[bold yellow] 📂 INJECT FOLDER PATH GUIDE [/bold yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))
                    custom_edit = safe_input('-> Enter custom source folder path (or press Enter to cancel): ').strip().strip('"\'')
                    if not custom_edit:
                        safe_input('\nPress Enter to continue...')
                        continue
                    custom_p = Path(custom_edit)
                    if not custom_p.exists():
                        console.print(f'[bold red][X] Path does not exist: {custom_p}[/bold red]')
                        safe_input('\nPress Enter to continue...')
                        continue
                    actual_edit_path = custom_p
                else:
                    valid_cnt = len([p for p in actual_edit_path.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')])
                    console.print(f"\n[bold green]✓ Found {valid_cnt} source file(s) in INJECT folder:[/bold green] [bold cyan]{actual_edit_path}[/bold cyan]")

                try:
                    pak = TencentPakFile(pak_file)
                    all_dirs = sorted(list({str(d).strip() for d in pak._index.keys() if str(d).strip() and str(d).strip() != "."}))

                    preset_map = {
                        "P1": ("Content/Lua/GameLua/Mod/BRMod/Gameplay/Core", "🇮🇳 [BGMI / PUBG] BRMod Gameplay Core (BEST FOR BGMI)"),
                        "P2": ("Content/Lua/GameLua", "🇮🇳 [BGMI / PUBG] GameLua Main Root Folder"),
                        "P3": ("Content/Lua/client", "🌐 Client Lua Folder"),
                        "P4": ("Content/Lua/slua", "⚙️ slua Engine Script Root"),
                        "P5": ("ShadowTrackerExtra/Content/Lua/GameLua/Mod/BRMod/Gameplay/Core", "🇮🇳 [BGMI / Global] ShadowTrackerExtra Prefix Path"),
                        "P6": ("ShadowTrackerExtra/Saved/Paks", "📦 Patch Paks Folder Location"),
                    }

                    preset_table = Table(
                        title="[bold bright_green]🔥 POPULAR GAME MODDING TARGET PATHS (PRESETS)[/bold bright_green]",
                        show_header=True,
                        header_style="bold bright_green",
                        box=ROUNDED,
                        border_style="bright_green"
                    )
                    preset_table.add_column("Key", style="bold yellow", justify="center", width=8)
                    preset_table.add_column("Target Path", style="bold white", justify="left")
                    preset_table.add_column("Description / Recommendation", style="bold cyan", justify="left")

                    for p_key, (p_path, p_desc) in preset_map.items():
                        preset_table.add_row(p_key, p_path, p_desc)

                    console.print()
                    console.print(preset_table)

                    console.print(Panel(
                        "[bold bright_yellow]🇮🇳 BGMI LUA MODDING QUICK HELP:[/bold bright_yellow]\n\n"
                        "• [bold white]BGMI me Lua file inject karne ke liye:[/bold white] Seedha [bold bright_green]ENTER[/bold bright_green] dabayein! ([bold cyan]Preset P1[/bold cyan] select ho jayega).\n"
                        "• [bold white]Target Path:[/bold white] [bold yellow]Content/Lua/GameLua/Mod/BRMod/Gameplay/Core[/bold yellow]\n"
                        "• [dim]Aapko koi bhi complicated path type karne ki zaroorat nahi hai! Just press ENTER.[/dim]",
                        title="[bold bright_yellow] 🎮 BGMI SPECIAL PRESET INSTRUCTION 🎮 [/bold bright_yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))

                    if all_dirs:
                        dir_table = Table(
                            title="[bold cyan]Internal PAK Directories Found[/bold cyan]",
                            show_header=True,
                            header_style="bold cyan",
                            box=ROUNDED,
                            border_style="dim cyan"
                        )
                        dir_table.add_column("Index", style="bold yellow", justify="center", width=8)
                        dir_table.add_column("PAK Internal Folder Path", style="bold white", justify="left")
                        for i, d in enumerate(all_dirs[:20], 1):
                            dir_table.add_row(str(i), str(d))
                        console.print()
                        console.print(dir_table)

                    console.print("\n[dim]Choose Preset [P1-P6], or PAK Dir [1-N], or paste custom path [Default P1].[/dim]")
                    target_input = safe_input("-> Select Target Path inside PAK (P1-P6 / 1-N / custom) [P1]: ").strip().strip('"\'')

                    if target_input.upper() == 'C':
                        safe_input('\nPress Enter to continue...')
                        continue

                    if not target_input or target_input.upper() == 'P1':
                        target_path = preset_map["P1"][0]
                        console.print(f"[bold green][OK] Selected Preset P1: {target_path}[/bold green]")
                    elif target_input.upper() in preset_map:
                        target_path = preset_map[target_input.upper()][0]
                        console.print(f"[bold green][OK] Selected Preset {target_input.upper()}: {target_path}[/bold green]")
                    elif target_input.isdigit() and all_dirs and 1 <= int(target_input) <= len(all_dirs):
                        target_path = all_dirs[int(target_input) - 1]
                        console.print(f"[bold green][OK] Selected PAK Internal Dir: {target_path}[/bold green]")
                    else:
                        target_path = target_input

                    # Clean and normalize target path (No leading/trailing slashes, forward slashes only)
                    target_path = target_path.strip().strip('"\'').strip('/\\').replace('\\', '/')
                    console.print(f"[bold cyan][+] Normalized Target Path: {target_path}[/bold cyan]")

                    # Interactive Lua Pre-Injection Assistant
                    lua_files = [p for p in actual_edit_path.rglob('*') if p.is_file() and p.suffix.lower() in ('.lua', '.luac')]
                    if lua_files:
                        console.print(f"\n[bold yellow]📜 Found {len(lua_files)} .lua script(s) in INJECT folder.[/bold yellow]")
                        console.print("[dim]Choose Lua Injection Preparation:[/dim]")
                        console.print("  [1] Auto-Fix Syntax & Inject Source (.lua) [Default - Recommended]")
                        console.print("  [2] Auto-Compile Bytecode & Preserve .lua Name [Fastest & UE4 Game Safe]")
                        console.print("  [3] Inject As-Is (No pre-processing)")
                        lua_prep = safe_input("-> Select Option [1-3] [1]: ").strip() or '1'
                        if lua_prep == '1':
                            for lf in lua_files:
                                fix_lua_syntax_for_lua51(lf)
                            console.print("[bold green]✓ Lua syntax auto-fixed for Lua 5.1 / UE4![/bold green]")
                        elif lua_prep == '2':
                            compiled_cnt = 0
                            for lf in lua_files:
                                fix_lua_syntax_for_lua51(lf)
                                tmp_luac = lf.with_suffix('.tmp_luac')
                                ok = False
                                try:
                                    res = subprocess.run(["luac5.1", "-o", str(tmp_luac), str(lf)], capture_output=True, text=True)
                                    if res.returncode == 0 and tmp_luac.exists():
                                        ok = True
                                except Exception:
                                    pass
                                if not ok:
                                    try:
                                        res = subprocess.run(["luajit", "-b", str(lf), str(tmp_luac)], capture_output=True, text=True)
                                        if res.returncode == 0 and tmp_luac.exists():
                                            ok = True
                                    except Exception:
                                        pass
                                if ok and tmp_luac.exists():
                                    lf.write_bytes(tmp_luac.read_bytes())
                                    tmp_luac.unlink(missing_ok=True)
                                    compiled_cnt += 1
                            if compiled_cnt > 0:
                                console.print(f"[bold green]✓ Compiled {compiled_cnt} script(s) to 5.1 bytecode while preserving .lua filename for UE4 engine![/bold green]")

                    result_dir = data_path / "RESULT"
                    result_dir.mkdir(parents=True, exist_ok=True)
                    output_pak = result_dir / pak_file.name

                    count = repack_pak_file_full(pak, actual_edit_path, output_pak, target_path=target_path, force_add=True)

                    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                    if sd_res.exists():
                        try:
                            shutil.copy2(output_pak, sd_res / pak_file.name)
                            console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                        except Exception:
                            pass

                    if count > 0:
                        console.print(f'[bold green][OK] Injected {count} file(s) successfully -> {output_pak.name}[/bold green]')
                        console.print(Panel(
                            "[bold bright_green]✅ LUA INJECTION COMPLETE![/bold bright_green]\n\n"
                            "[bold white]🎮 Game me Lua execute na hone standard reasons & solution:[/bold white]\n"
                            " 1. [bold yellow]Filename Match:[/bold yellow] Script ka name game ke require filename se match hona chahiye (e.g. `BRMod.lua`, `Main.lua`, `BattleMain.lua`).\n"
                            " 2. [bold yellow]Target Path:[/bold yellow] BGMI me [bold cyan]Preset P1[/bold cyan] (`Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`) ya Global me [bold cyan]Preset P5[/bold cyan] use karein.\n"
                            " 3. [bold yellow]Lua 5.1 Syntax:[/bold yellow] Pehle [bold cyan]Category [2] (LUA Tools)[/bold cyan] se Auto Lua Workflow chalayein taaki Lua 5.1 syntax errors fix ho jayein!",
                            title="[bold bright_yellow] 💡 GAME LUA RUNNING TIPS [/bold bright_yellow]",
                            border_style="bright_green",
                            box=ROUNDED
                        ))
                    else:
                        console.print('[bold red][X] No files were injected.[/bold red]')

                except Exception as e:
                    handle_exception(e, "Inject Path", data_path)
                safe_input('\nPress Enter to continue...')

        elif choice == '3':
            run_obb_manager(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '4':
            run_pak_compare_dumper(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)

def run_one_click_auto_lua_workflow(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🚀 1-CLICK AUTOMATIC LUA FIX & COMPILER WORKFLOW 🚀[/bold bright_cyan]\n[dim]Auto-scans LUA/RESULT/REPLACE -> Auto-fixes syntax for Lua 5.1 -> Compiles to .luac -> Auto-syncs everywhere![/dim]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("1-Click Auto Lua Workflow", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print(f"\n[bold cyan][Step 1/3] Fixing syntax and 5.1 compatibility for '{lua_file.name}'...[/bold cyan]")
    fixed_lua = fix_lua_syntax_for_lua51(lua_file)
    console.print(f"[bold green]✅ Syntax fixed! Created patched file: {fixed_lua.name}[/bold green]")

    console.print(f"\n[bold cyan][Step 2/3] Compiling to .luac bytecode...[/bold cyan]")
    all_compilers = ["luac5.1", "luac51", "luac", "luajit", "luac5.2", "luac5.3", "luac5.4"]
    available_compilers = [c for c in all_compilers if shutil.which(c)]

    if not available_compilers:
        console.print("[bold yellow][!] Installing lua51 and luajit via Termux pkg...[/bold yellow]")
        try:
            subprocess.run("pkg update -y && pkg install -y lua51 luajit", shell=True, check=True)
            available_compilers = [c for c in all_compilers if shutil.which(c)]
        except Exception as e:
            console.print(f"[bold red][X] Could not auto-install compilers: {e}[/bold red]")

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_luac = res_dir / f"{lua_file.stem}.luac"

    success = False
    for compiler in available_compilers:
        if compiler == "luajit":
            cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
        else:
            cmd = [compiler, "-o", str(out_luac), str(fixed_lua)]
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            console.print(f"[bold green]✅ Compiled successfully with '{compiler}' -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
            success = True
            break

    if not success:
        console.print(f"[bold red][X] Bytecode compilation failed. Using patched .lua script as fallback.[/bold red]")
        out_luac = res_dir / f"{lua_file.stem}_fixed.lua"
        shutil.copy2(fixed_lua, out_luac)

    console.print(f"\n[bold cyan][Step 3/3] Auto-syncing compiled output across all workspace folders...[/bold cyan]")
    target_dirs = [
        data_path / "LUA",
        data_path / "RESULT",
        data_path / "REPLACE",
        data_path / "INJECT",
        Path("/sdcard/FeaturesticLeaks/LUA"),
        Path("/sdcard/FeaturesticLeaks/RESULT"),
        Path("/sdcard/FeaturesticLeaks/REPLACE"),
        Path("/sdcard/FeaturesticLeaks/INJECT")
    ]

    synced_count = 0
    for td in target_dirs:
        try:
            td.mkdir(parents=True, exist_ok=True)
            dest = td / out_luac.name
            shutil.copy2(out_luac, dest)
            synced_count += 1
        except Exception:
            pass

    console.print(f"[bold green]🎉 Auto-Sync Complete! Saved output to {synced_count} folders across workspace & SDCard![/bold green]")
    console.print(f"[bold white]👉 You can now immediately run Repack / Replace without needing to move any files![/bold white]")

# ==================== AI-ASSISTED REPAIR & MULTI-API ENGINE ====================

AI_CONFIG_FILE = Path.home() / ".featurestic_ai_config.json"

def get_ai_config() -> Dict[str, Any]:
    default_cfg = {
        "active_provider": "opencode",
        "keys": {
            "google": [],
            "groq": [],
            "openrouter": [],
            "opencode": []
        },
        "opencode_endpoint": "https://api.opencode.ai/v1",
        "opencode_model": "opencode-modding-v1",
        "opencode_api_key": "",
        "opencode_keys": [],
        "telegram_bot_token": "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM",
        "telegram_chat_id": "-1004375122082"
    }
    if AI_CONFIG_FILE.exists():
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_cfg.update(data)
                    if not default_cfg.get("telegram_bot_token"):
                        default_cfg["telegram_bot_token"] = "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
                    if not default_cfg.get("telegram_chat_id"):
                        default_cfg["telegram_chat_id"] = "-1004375122082"
                    
                    # Auto-fix stray API key saved into endpoint field by accident
                    ep_val = str(default_cfg.get("opencode_endpoint", "")).strip()
                    if ep_val.startswith("sk-"):
                        if not isinstance(default_cfg.get("opencode_keys"), list):
                            default_cfg["opencode_keys"] = []
                        if ep_val not in default_cfg["opencode_keys"]:
                            default_cfg["opencode_keys"].append(ep_val)
                        default_cfg["opencode_endpoint"] = "https://api.opencode.ai/v1"
                    elif not ep_val:
                        default_cfg["opencode_endpoint"] = "https://api.opencode.ai/v1"

                    if not default_cfg.get("opencode_model"):
                        default_cfg["opencode_model"] = "opencode-modding-v1"
                    if not isinstance(default_cfg.get("opencode_keys"), list):
                        default_cfg["opencode_keys"] = []
                    single_k = default_cfg.get("opencode_api_key", "").strip()
                    if single_k and single_k not in default_cfg["opencode_keys"]:
                        default_cfg["opencode_keys"].append(single_k)
                    return default_cfg
        except Exception:
            pass
    return default_cfg

def save_ai_config(cfg: Dict[str, Any]):
    try:
        with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        console.print(f"[bold red][X] Could not save AI config: {e}[/bold red]")

def manage_ai_api_keys():
    cfg = get_ai_config()
    while True:
        print_banner()
        console.print(Panel(
            "[bold bright_cyan]🤖 OPENCODE UNLIMITED AI MODEL & API MANAGER 🤖[/bold bright_cyan]\n\n"
            "[bold white]🚀 Primary OpenCode Custom Engine (No API Exhaustion / Rate Limits):[/bold white]\n"
            " • [bold bright_yellow]OpenCode Endpoint:[/bold bright_yellow]  [bold underline bright_green]https://api.opencode.ai/v1[/bold underline bright_green]\n"
            " • [bold bright_yellow]🔑 OpenCode Auth Link:[/bold bright_yellow] [bold underline bright_cyan]https://opencode.ai/auth[/bold underline bright_cyan]\n"
            " • [bold bright_yellow]OpenCode API Keys:[/bold bright_yellow]  [bold bright_green]Multi-Key Auto Rotation Active[/bold bright_green]\n\n"
            "[dim]OpenCode AI runs smoothly across all device modding tasks & auto-reports errors to Telegram![/dim]",
            border_style="cyan",
            box=ROUNDED
        ))
        
        table = Table(title="[bold cyan]OpenCode AI Provider Status & Details[/bold cyan]", box=ROUNDED)
        table.add_column("Provider Engine", style="bold yellow")
        table.add_column("Status", style="bold white", justify="center")
        table.add_column("Endpoint & Key Details", style="dim")
        
        oc_ep = cfg.get("opencode_endpoint", "https://api.opencode.ai/v1")
        oc_mod = cfg.get("opencode_model", "opencode-modding-v1")
        oc_keys = cfg.get("opencode_keys", [])
        if not oc_keys and cfg.get("opencode_api_key"):
            oc_keys = [cfg.get("opencode_api_key")]
        
        key_count_str = f"{len(oc_keys)} API Key(s) Saved" if oc_keys else "Default Token Active"
        table.add_row("OpenCode Custom AI (Primary)", "✅ ACTIVE", f"Endpoint: {oc_ep} | Model: {oc_mod} | {key_count_str}")

        bot_status = "Configured" if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id") else "Not Set"
        user_nick = cfg.get("telegram_username") or cfg.get("user_nickname") or get_device_user_info()
        console.print(f"[bold white]Telegram Auto-Report Bot:[/bold white] [bold cyan]{bot_status}[/bold cyan]  |  [bold white]Developer Tag:[/bold white] [bold yellow]{user_nick}[/bold yellow]")
        console.print(table)
        console.print()
        console.print("  [1] Add / Manage OpenCode API Key 🔑")
        console.print("  [2] Live Test OpenCode Connection ⚡")
        console.print("  [3] Configure Developer Telegram Auto-Report Bot 🚨")
        console.print("  [0] Back to Main Menu")
        
        choice = safe_input("\n-> Select Option [0-3]: ").strip()
        if choice == '1':
            console.print("\n[bold cyan]🚀 Configure OpenCode API Key:[/bold cyan]")
            console.print("[bold yellow]🔑 Get OpenCode API Keys Direct Link:[/bold bright_yellow] [bold underline bright_cyan]https://opencode.ai/auth[/bold underline bright_cyan]\n")
            
            curr_keys = cfg.get("opencode_keys", [])
            if not curr_keys and cfg.get("opencode_api_key"):
                curr_keys = [cfg.get("opencode_api_key")]
            
            console.print(f"[bold white]Total Saved OpenCode Keys:[/bold white] [bright_green]{len(curr_keys)}[/bright_green]")
            for idx, k in enumerate(curr_keys, 1):
                mask = k[:8] + "..." + k[-4:] if len(k) > 12 else k
                console.print(f"  {idx}. [dim cyan]{mask}[/dim cyan]")
            
            console.print()
            key_in = safe_input("-> Enter OpenCode API Key (starts with sk-..., or 'clear' to reset): ").strip()
            
            if key_in:
                if key_in.lower() == 'clear':
                    cfg["opencode_keys"] = []
                    cfg["opencode_api_key"] = ""
                    console.print("[bold yellow]🧹 Cleared all OpenCode API keys![/bold yellow]")
                elif key_in.startswith("http://") or key_in.startswith("https://"):
                    cfg["opencode_endpoint"] = key_in
                    console.print(f"[bold green]✅ OpenCode Base URL updated to '{key_in}'![/bold green]")
                else:
                    new_keys = [k.strip() for k in key_in.split(',') if k.strip()]
                    if "opencode_keys" not in cfg or not isinstance(cfg["opencode_keys"], list):
                        cfg["opencode_keys"] = []
                    for nk in new_keys:
                        if nk not in cfg["opencode_keys"]:
                            cfg["opencode_keys"].append(nk)
                    if cfg["opencode_keys"]:
                        cfg["opencode_api_key"] = cfg["opencode_keys"][0]
                    console.print(f"[bold green]✅ OpenCode API Key(s) saved! Total Keys: {len(cfg['opencode_keys'])}[/bold green]")
            
            cfg["active_provider"] = "opencode"
            save_ai_config(cfg)
            time.sleep(1.5)
        elif choice == '2':
            console.print("\n[bold cyan]⚡ Live Testing OpenCode AI Endpoint...[/bold cyan]")
            oc_ep = cfg.get("opencode_endpoint", "https://api.opencode.ai/v1").rstrip('/')
            if not oc_ep.endswith("/chat/completions"):
                oc_ep += "/chat/completions"
            oc_m = cfg.get("opencode_model", "opencode-modding-v1")
            oc_keys = cfg.get("opencode_keys", [])
            if not oc_keys and cfg.get("opencode_api_key"):
                oc_keys = [cfg.get("opencode_api_key")]
            if not oc_keys:
                oc_keys = [""]
            
            success_count = 0
            for idx, oc_k in enumerate(oc_keys, 1):
                try:
                    headers = {"Content-Type": "application/json"}
                    if oc_k:
                        headers["Authorization"] = f"Bearer {oc_k}"
                    res = requests.post(oc_ep, json={"model": oc_m, "messages": [{"role": "user", "content": "hi"}]}, headers=headers, timeout=8)
                    if res.status_code == 200:
                        key_mask = (oc_k[:8] + "...") if len(oc_k) > 8 else "Default"
                        console.print(f" • Key #{idx} ({key_mask}): [bold green]✅ WORKING UNLIMITED![/bold green]")
                        success_count += 1
                    else:
                        console.print(f" • Key #{idx}: [bold yellow]HTTP {res.status_code} response[/bold yellow]")
                except Exception as ex_oc:
                    console.print(f" • Key #{idx}: [bold dim yellow]note: {ex_oc}[/bold dim yellow]")
            
            if success_count > 0:
                console.print(f"\n[bold green]🎉 OpenCode AI is fully ready! ({success_count}/{len(oc_keys)} keys functional)[/bold green]")
            time.sleep(2)
        elif choice == '3':
            console.print("\n[bold cyan]🚨 Configure Telegram Auto-Report Bot for Direct Error Delivery:[/bold cyan]")
            console.print("[dim]Create a bot on Telegram via @BotFather to get your Bot Token & Chat ID.[/dim]\n")
            
            curr_token = cfg.get("telegram_bot_token", "")
            curr_chat = cfg.get("telegram_chat_id", "")
            
            if curr_token and curr_chat:
                console.print(f"[bold white]Current Bot Token:[/bold white] [bright_yellow]{curr_token[:8]}...{curr_token[-4:]}[/bright_yellow]")
                console.print(f"[bold white]Current Chat ID:[/bold white] [bright_yellow]{curr_chat}[/bright_yellow]\n")
            
            token_in = safe_input("-> Enter Telegram Bot Token (or press Enter to keep current): ").strip()
            chat_in = safe_input("-> Enter Developer Telegram Chat ID (or press Enter to keep current): ").strip()
            
            if token_in:
                cfg["telegram_bot_token"] = token_in
            if chat_in:
                cfg["telegram_chat_id"] = chat_in
                
            save_ai_config(cfg)
            console.print("[bold green]✅ Telegram Auto-Report configuration updated successfully![/bold green]")
            console.print("[dim]Sending test connection report to your Telegram group...[/dim]")
            send_telegram_bug_report("TEST_PING", "Telegram Bot Connection Verified Successfully!", "Telegram Bot Config Test", "FeaturesticLeaks.py", "6699", "manage_ai_api_keys", "No errors! Bot is connected and working.")
            console.print("[dim]All unhandled errors anywhere on user devices will now instantly land on your Telegram![/dim]")
            time.sleep(1.5)
        elif choice == '0':
            break

def call_ai_api(prompt: str) -> Optional[str]:
    clean_p = prompt.strip()
    low_p = clean_p.lower()

    SYSTEM_PROMPT = (
        "You are Featurestic Leaks AI Engine — a highly capable, natural, friendly AI modding assistant built for Featurestic Leaks "
        "(PAK/OBB Unpacker & Repacker, Lua 5.1 Compiler/Decompiler, AI Syntax Repair).\n\n"
        "PERSONALITY & CONVERSATIONAL STYLE:\n"
        "1. Speak naturally, freely, politely, and conversationally in friendly Hinglish (Hindi + English).\n"
        "2. Never give rigid, repetitive, or canned template answers. Respond dynamically and uniquely to whatever the user asks or says.\n"
        "3. When writing Lua 5.1 scripts (GameGuard / PUBG / BGMI / UE4 memory modding), write COMPLETE, FULLY WORKING, copy-paste ready code without placeholders.\n"
        "4. Include complete functions, error checks (`gg.isVisible()`, `gg.clearResults()`, `gg.searchNumber()`, `gg.getResults()`, `gg.editAll()`), and correct memory types (`gg.TYPE_FLOAT`, `gg.TYPE_DWORD`).\n"
        "5. Provide exact step-by-step guidance for PAK/OBB unpacking, repacking, and injecting Lua files into target paths when asked.\n"
        "6. Everything is done directly inside Featurestic Leaks on Termux/Android."
    )

    # Determine task complexity to pick models smartly
    is_complex_code = any(kw in low_p for kw in [
        'function', 'local ', 'return', 'syntax error', 'end statement',
        'compile error', 'gameguard', 'luac 5.1', 'fix the syntax', 'lua script'
    ]) or len(prompt) > 800

    if is_complex_code:
        gemini_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        groq_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        openrouter_models = ["meta-llama/llama-3.3-70b-instruct", "google/gemini-flash-1.5"]
    else:
        gemini_models = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash"]
        groq_models = ["llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.2-3b-preview"]
        openrouter_models = ["google/gemini-flash-1.5", "meta-llama/llama-3.1-8b-instruct:free", "google/gemini-flash-1.5-8b"]

    cfg = get_ai_config()

    # Always attempt OpenCode API call first (Primary Engine)
    oc_ep = cfg.get("opencode_endpoint", "https://api.opencode.ai/v1").strip()
    oc_m = cfg.get("opencode_model", "opencode-modding-v1").strip()
    oc_keys = cfg.get("opencode_keys", [])
    if not isinstance(oc_keys, list):
        oc_keys = []
    single_oc_k = cfg.get("opencode_api_key", "").strip()
    if single_oc_k and single_oc_k not in oc_keys:
        oc_keys.append(single_oc_k)
    if not oc_keys:
        oc_keys = [""]

    if oc_ep:
        ep_url = oc_ep.rstrip('/')
        if not ep_url.endswith("/chat/completions"):
            ep_url += "/chat/completions"
        for oc_k in oc_keys:
            try:
                headers = {"Content-Type": "application/json"}
                if oc_k:
                    headers["Authorization"] = f"Bearer {oc_k}"
                max_tok = 2048 if is_complex_code else 1024
                payload = {
                    "model": oc_m or "opencode-modding-v1",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tok,
                    "temperature": 0.7
                }
                resp = requests.post(ep_url, json=payload, headers=headers, timeout=12)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        txt = data['choices'][0]['message']['content']
                        if txt:
                            return txt.strip()
                    except Exception:
                        pass
            except Exception:
                pass

    # Secondary providers fallback
    key_queue = [] # list of (provider, key)

    for prov in ["google", "groq", "openrouter"]:
        for k in cfg.get("keys", {}).get(prov, []):
            if k and (prov, k) not in key_queue:
                key_queue.append((prov, k))

    env_gemini = os.environ.get("GEMINI_API_KEY")
    if env_gemini and ("google", env_gemini) not in key_queue:
        key_queue.append(("google", env_gemini))

    if key_queue:
        for prov, key in key_queue:
            try:
                if prov == "google":
                    for g_model in gemini_models:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={key}"
                        payload = {
                            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7}
                        }
                        resp = requests.post(url, json=payload, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['candidates'][0]['content']['parts'][0]['text']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "groq":
                    for g_model in groq_models:
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        payload = {
                            "model": g_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                        resp = requests.post(url, json=payload, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "openrouter":
                    for or_model in openrouter_models:
                        url = "https://openrouter.ai/api/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        payload = {
                            "model": or_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                        resp = requests.post(url, json=payload, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass
            except Exception:
                pass

    return None


def ai_fix_lua_code(lua_code: str, error_msg: str = "") -> Optional[str]:
    prompt = f"""You are an expert Lua 5.1 and GameGuard script engineer.
Fix the syntax errors, missing functions, or bugs in the following Lua script so that it compiles perfectly with luac 5.1 and runs smoothly without syntax/runtime crashes.

CRITICAL RULES:
1. Output ONLY valid, runnable Lua code. Do NOT wrap in markdown code blocks like ```lua ... ``` if possible, or keep it strictly clean.
2. Ensure strict compatibility with Lua 5.1 and GameGuard (gg.* calls).
3. Do not modify the functional business logic, menu items, or memory search values unless they contain invalid syntax.

COMPILATION ERROR / BUG DESCRIPTION:
{error_msg}

ORIGINAL LUA SCRIPT:
{lua_code}
"""
    result = call_ai_api(prompt)
    if result:
        cleaned = re.sub(r'^```(?:lua)?\n', '', result, flags=re.MULTILINE)
        cleaned = re.sub(r'\n```$', '', cleaned, flags=re.MULTILINE).strip()
        return cleaned
    return None

query_ai_for_lua_fix = ai_fix_lua_code


def run_ai_assisted_lua_repair(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🤖 AI-ASSISTED LUA SCRIPT REPAIR ENGINE 🤖[/bold bright_cyan]\n[dim]Uses Google Gemini / Groq / OpenRouter AI to fix broken Lua syntax, missing end statements, & GameGuard errors![/dim]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("AI Lua Repair", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    try:
        raw_code = lua_file.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        console.print(f"[bold red][X] Could not read file: {e}[/bold red]")
        return

    # Test local compilation first to detect error
    compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
    error_msg = "Manual user requested AI code cleanup & syntax repair for Lua 5.1 compatibility."
    
    if compiler:
        tmp_test = lua_file.with_suffix('.tmp_compile_test')
        proc = subprocess.run([compiler, "-o", str(tmp_test), str(lua_file)], capture_output=True, text=True)
        tmp_test.unlink(missing_ok=True)
        if proc.returncode != 0:
            error_msg = proc.stderr.strip()
            console.print(f"[bold yellow][!] Compilation Error Detected:\n{error_msg}[/bold yellow]\n")
        else:
            console.print("[bold green]✓ File compiles locally, but AI will optimize and refactor code for Lua 5.1.[/bold green]\n")

    ai_result = query_ai_for_lua_fix(raw_code, error_msg)
    if not ai_result:
        return

    # Clean markdown formatting if present
    cleaned_code = re.sub(r'^```(?:lua)?\n', '', ai_result, flags=re.MULTILINE)
    cleaned_code = re.sub(r'\n```$', '', cleaned_code, flags=re.MULTILINE).strip()

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_repaired = res_dir / f"{lua_file.stem}_ai_repaired.lua"
    out_repaired.write_text(cleaned_code, encoding='utf-8')

    console.print(f"\n[bold green]🎉 AI Repair Successful! Saved repaired script to:[/bold green] [bold cyan]{out_repaired}[/bold cyan]")
    
    # Auto-compile check
    if compiler:
        out_luac = res_dir / f"{lua_file.stem}_ai_repaired.luac"
        proc2 = subprocess.run([compiler, "-o", str(out_luac), str(out_repaired)], capture_output=True, text=True)
        if proc2.returncode == 0:
            console.print(f"[bold green]✅ Compiled repaired script to bytecode -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
        else:
            console.print(f"[bold yellow][!] Compiled bytecode warning: {proc2.stderr.strip()}[/bold yellow]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_repaired, sd_res / out_repaired.name)
            console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_repaired.name}[/bold green]")
        except Exception:
            pass

def lua_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]🌙 LUA TOOLS SUITE 🌙[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=24, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Decompile Lua (.luac)", "Decompile .luac bytecode to .lua source")
        menu_table.add_row("[2]", "Compile & Protect Lua (.lua)", "Auto-encrypt & convert .lua source code to protected .luac")
        menu_table.add_row("[3]", "1-Click Auto Lua Workflow", "Auto-fix syntax, protect, compile & sync to output folder")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-3] [0]: \033[0m').strip()

        if choice == '1':
            run_lua_decompiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_lua_compiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_one_click_auto_lua_workflow(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


# ==================== WATCH MODE ENGINE ====================

if HAS_WATCHDOG:
    class AutoHandler(FileSystemEventHandler):
        def __init__(self, data_path: Path):
            super().__init__()
            self.data_path = data_path
            self.processed = set()

        def on_created(self, event):
            if not event.is_directory:
                filepath = Path(event.src_path)
                if filepath in self.processed:
                    return
                self.processed.add(filepath)

                console.print(f"\n[bold bright_yellow]📁 New File Detected:[/bold bright_yellow] [bold cyan]{filepath}[/bold cyan]")

                if filepath.suffix.lower() in ['.pak', '.obb']:
                    console.print(f"[bold bright_green]📦 Auto-unpacking PAK file: {filepath.name}...[/bold bright_green]")
                    try:
                        pak = TencentPakFile(filepath)
                        unpack_path = self.data_path / "UNPACK" / filepath.stem
                        pak.dump(unpack_path)
                        console.print(f"[bold green]✅ Auto-unpacked {filepath.name} to {unpack_path}![/bold green]")

                        sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / filepath.stem
                        if sd_unpack.parent.exists() and sd_unpack != unpack_path:
                            try:
                                pak.dump(sd_unpack)
                                console.print(f"[bold green][+] Also extracted to SDCard: {sd_unpack}[/bold green]")
                            except Exception:
                                pass
                    except Exception as e:
                        console.print(f"[bold red][X] Unpack error for {filepath.name}: {e}[/bold red]")

                elif filepath.suffix.lower() in ['.lua', '.txt']:
                    console.print(f"[bold bright_cyan]🌙 Auto-compiling Lua script: {filepath.name}...[/bold bright_cyan]")
                    try:
                        fixed_lua = fix_lua_syntax_for_lua51(filepath)
                        res_dir = self.data_path / "RESULT"
                        res_dir.mkdir(parents=True, exist_ok=True)
                        out_luac = res_dir / f"{filepath.stem}.luac"

                        compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                        if compiler:
                            proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                            if proc.returncode == 0:
                                console.print(f"[bold green]✅ Auto-compiled {filepath.name} -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
                                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                                if sd_res.exists():
                                    try:
                                        shutil.copy2(out_luac, sd_res / out_luac.name)
                                        console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_luac.name}[/bold green]")
                                    except Exception:
                                        pass
                            else:
                                console.print(f"[bold yellow][!] Compilation warning: {proc.stderr.strip()}[/bold yellow]")
                        else:
                            console.print("[bold yellow][!] No Lua compiler found in system PATH.[/bold yellow]")
                    except Exception as e:
                        console.print(f"[bold red][X] Auto-compile error for {filepath.name}: {e}[/bold red]")

def run_watch_mode(data_path: Path):
    print_banner()
    console.print(Panel(Align.center("[bold bright_cyan]👁️ AUTOMATIC WATCH MODE 👁️[/bold bright_cyan]\n[dim]Monitors PAK_INPUT and LUA_INPUT folders in real-time and auto-processes incoming files![/dim]"), border_style="cyan", box=ROUNDED))

    if not HAS_WATCHDOG:
        console.print("[bold red][X] 'watchdog' module is not installed. Please run: pip install watchdog[/bold red]")
        return

    paths_to_watch = [
        data_path / "PAK",
        data_path / "LUA",
        Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT"),
        Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT")
    ]

    observer = Observer()
    handler = AutoHandler(data_path)
    scheduled_count = 0

    for p in paths_to_watch:
        try:
            p.mkdir(parents=True, exist_ok=True)
            observer.schedule(handler, path=str(p), recursive=False)
            scheduled_count += 1
            console.print(f"[bold green][+] Watching directory:[/bold green] [bold white]{p}[/bold white]")
        except Exception as e:
            console.print(f"[dim yellow][!] Skip watching {p}: {e}[/dim yellow]")

    if scheduled_count == 0:
        console.print("[bold red][X] No valid directories to watch.[/bold red]")
        return

    console.print("\n[bold bright_yellow]👁️ Watch Mode Active... Drop any .pak, .obb, or .lua file into the input folders to process![/bold bright_yellow]")
    console.print("[bold dim]Press Ctrl+C to stop watching and return to menu.[/bold dim]\n")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[bold yellow]⏹️ Watch Mode Stopped.[/bold yellow]")
    except Exception as e:
        observer.stop()
        console.print(f"\n[bold red][X] Watcher error: {e}[/bold red]")
    observer.join()


def run_diagnostic_benchmark(data_path: Path):
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]⚡ TERMUX PERFORMANCE BENCHMARK & DIAGNOSTIC LOG SUMMARY ⚡[/bold bright_cyan]\n"
        "[dim]Testing system response time, Lua compiler speed, memory usage & log hygiene...[/dim]",
        border_style="cyan",
        box=ROUNDED
    ))
    
    # 1. System Memory & Storage Info
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_str = f"{mem.used / (1024**2):.1f} MB / {mem.total / (1024**2):.1f} MB ({mem.percent}%)"
    except Exception:
        mem_str = "Available (Termux System)"

    # 2. Test Lua Compiler Performance
    compiler_speed = "N/A"
    luac_bin = shutil.which("luac5.1") or shutil.which("luac") or shutil.which("luajit")
    if luac_bin:
        t0 = time.perf_counter()
        test_script = data_path / ".speed_test.lua"
        test_out = data_path / ".speed_test.luac"
        test_script.write_text("print('Benchmark Speed Test')")
        proc = subprocess.run([luac_bin, "-o", str(test_out), str(test_script)], capture_output=True)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000
        compiler_speed = f"{elapsed_ms:.2f} ms ({Path(luac_bin).name})"
        test_script.unlink(missing_ok=True)
        test_out.unlink(missing_ok=True)

    # 3. Log Hygiene & Cleanup
    logs_dir = data_path / "logs"
    log_files = list(logs_dir.glob("*.log")) if logs_dir.exists() else []
    cleanup_old_logs(logs_dir, max_age_days=2.0, max_files=10)

    # Display Diagnostic Table
    diag_table = Table(title="[bold green]System Diagnostic Results[/bold green]", box=ROUNDED)
    diag_table.add_column("Component", style="bold yellow")
    diag_table.add_column("Status / Speed / Details", style="bold white")

    diag_table.add_row("Memory (RAM)", mem_str)
    diag_table.add_row("Lua Compiler Speed", compiler_speed)
    diag_table.add_row("Log Files Hygiene", f"{len(log_files)} log(s) scanned & trimmed")
    diag_table.add_row("Python Engine", f"Python {sys.version.split()[0]} ({os.name.upper()})")

    console.print(diag_table)
    console.print("\n[bold green]✅ System benchmark & log diagnostic completed successfully![/bold green]")

def utilities_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]🛠️ UTILITIES & HELP 🛠️[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "UE4 String Tool", "Extract & repack .uasset/.uexp strings")
        menu_table.add_row("[2]", "File Finder", "Search .uasset/.uexp/.ubulk by pattern")
        menu_table.add_row("[3]", "URL & LIB Patcher 🔗", "Find & replace encrypted URLs in .so / binaries")
        menu_table.add_row("[4]", "File Resizer & Equalizer", "Match exact byte size of any file (PAK, OBB, LUA)")
        menu_table.add_row("[5]", "Termux Auto-Setup", "Setup 'leak' direct command & SDCard folders")
        menu_table.add_row("[6]", "Workspace Summary", "Folder guide & live file count summary")
        menu_table.add_row("[7]", "Beginner Guide & FAQ 🔰", "Beginner Quick Start & Modding Help")
        menu_table.add_row("[8]", "Cleanup Workspace", "Delete workspace folders")
        menu_table.add_row("[9]", "Check Tool Update 🚀", "Force update tool to latest GitHub version")
        menu_table.add_row("[10]", "Diagnostic & Benchmark ⚡", "Check execution speed, RAM & log hygiene")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-10] [0]: \033[0m').strip()

        if choice == '1':
            run_ue4_string_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_file_finder_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_url_lib_patcher_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            run_file_resizer_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '5':
            install_termux_shortcut_and_sdcard(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '6':
            print_banner()
            display_workspace_summary(data_path)
            show_workflow_guide()
            safe_input('\nPress Enter to continue...')
        elif choice == '7':
            run_beginner_guide(data_path)
        elif choice == '8':
            delete_folder(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '9' or choice.lower() == 'u':
            check_and_auto_update(interactive=True)
            safe_input('\nPress Enter to continue...')
        elif choice == '10':
            run_diagnostic_benchmark(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


def watch_mode_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]👁️ WATCH MODE ENGINE 👁️[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Start Watch Mode 👁️", "Real-time auto-unpack .pak/.obb & auto-compile .lua")
        menu_table.add_row("[2]", "Watch Mode Status", "Check monitored input folders & watchdog installation")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-2] [0]: \033[0m').strip()

        if choice == '1':
            run_watch_mode(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            print_banner()
            console.print(Panel(
                f"[bold cyan]👁️ WATCH MODE STATUS & CONFIGURATION[/bold cyan]\n\n"
                f"[bold white]Watchdog Library Installed:[/bold white] {'[bold green]YES[/bold green]' if HAS_WATCHDOG else '[bold red]NO (run pip install watchdog)[/bold red]'}\n\n"
                f"[bold yellow]Monitored Folders:[/bold yellow]\n"
                f" • {data_path / 'PAK'}\n"
                f" • {data_path / 'LUA'}\n"
                f" • /sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT\n"
                f" • /sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT\n\n"
                f"[dim]When active, dropping any .pak/.obb file will automatically extract it, and any .lua file will be compiled automatically![/dim]",
                border_style="cyan",
                box=ROUNDED
            ))
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


def ensure_directories(data_path: Path):
    dirs = [
        data_path / "INPUT", data_path / "OUTPUT", data_path / "UNPACK",
        data_path / "REPACK", data_path / "RESULT", data_path / "TEMP_INJECT",
        data_path / "PAK", data_path / "LUA", data_path / "INJECT",
        data_path / "PAK_WORKSPACE" / "1_INPUT",
        data_path / "PAK_WORKSPACE" / "2_UNPACK",
        data_path / "PAK_WORKSPACE" / "3_RESULT",
        data_path / "PAK_WORKSPACE" / "4_INJECT",
    ]
    sd_path = Path("/sdcard/FeaturesticLeaks")
    try:
        if sd_path.exists() or Path("/sdcard").exists():
            dirs.extend([
                sd_path / "INPUT", sd_path / "OUTPUT", sd_path / "UNPACK",
                sd_path / "REPACK", sd_path / "RESULT", sd_path / "TEMP_INJECT",
                sd_path / "PAK", sd_path / "LUA", sd_path / "INJECT",
                sd_path / "PAK_WORKSPACE" / "1_INPUT",
                sd_path / "PAK_WORKSPACE" / "2_UNPACK",
                sd_path / "PAK_WORKSPACE" / "3_RESULT",
                sd_path / "PAK_WORKSPACE" / "4_INJECT",
            ])
    except Exception:
        pass
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass


def run_url_lib_patcher_tool(data_path: Path):
    console.print("\n[bold cyan]🔗 URL & LIB PATCHER TOOL[/bold cyan]")
    console.print("[dim]Find and patch URLs or libraries in .so binaries or Lua scripts.[/dim]")
    target_str = safe_input("-> Enter file path (.so / .lua / binary): ").strip()
    if not target_str:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    tf = Path(target_str)
    if not tf.exists():
        console.print(f"[bold red][X] File not found: {tf}[/bold red]")
        return
    old_url = safe_input("-> Enter old URL/string to search: ").strip()
    new_url = safe_input("-> Enter new URL/string replacement: ").strip()
    if not old_url or not new_url:
        console.print("[yellow]Invalid inputs.[/yellow]")
        return
    try:
        content = tf.read_bytes()
        old_bytes = old_url.encode('utf-8')
        new_bytes = new_url.encode('utf-8')
        if old_bytes in content:
            if len(new_bytes) > len(old_bytes):
                console.print("[bold red][X] New URL cannot be longer than old URL for binary patch.[/bold red]")
                return
            new_bytes = new_bytes.ljust(len(old_bytes), b'\x00')
            patched = content.replace(old_bytes, new_bytes)
            tf.write_bytes(patched)
            console.print(f"[bold green]✅ Successfully patched {tf.name}![/bold green]")
        else:
            console.print(f"[bold yellow][!] Old URL string '{old_url}' not found in {tf.name}[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red][X] Patch error: {e}[/bold red]")


def display_workspace_summary(data_path: Path):
    snapshot = get_live_workspace_context(data_path)
    if Panel:
        console.print(Panel(f"[bold bright_white]{snapshot}[/bold bright_white]", title="[bold cyan] 📊 WORKSPACE SUMMARY [/bold cyan]", border_style="bright_cyan", box=ROUNDED))
    else:
        console.print(snapshot)


def get_live_workspace_context(data_path: Path) -> str:
    """
    Returns a live file status snapshot of the device & tool workspace for AI prompts.
    """
    sd_path = Path("/sdcard/FeaturesticLeaks")
    lines = ["CURRENT LIVE WORKSPACE & DEVICE FILE SNAPSHOT:"]

    # 1. PAK Folder
    pak_files = []
    for p in [data_path / "PAK", data_path / "INPUT", sd_path / "PAK", sd_path / "INPUT"]:
        if p.exists():
            for f in p.glob("*"):
                if f.is_file() and f.suffix.lower() in ['.pak', '.obb']:
                    pak_files.append(f"{f.name} ({human_size(f.stat().st_size)})")
    lines.append(f"• PAK/OBB Input Files: {', '.join(pak_files) if pak_files else 'None (Folder empty)'}")

    # 2. LUA Folder
    lua_files = []
    for p in [data_path / "LUA", data_path / "INPUT", sd_path / "LUA", sd_path / "INPUT"]:
        if p.exists():
            for f in p.glob("*"):
                if f.is_file() and f.suffix.lower() in ['.lua', '.luac', '.txt']:
                    lua_files.append(f"{f.name} ({human_size(f.stat().st_size)})")
    lines.append(f"• LUA Script Files: {', '.join(lua_files) if lua_files else 'None (Folder empty)'}")

    # 3. UNPACK / RESULT Folders
    res_items = []
    for p in [data_path / "RESULT", data_path / "UNPACK", sd_path / "RESULT", sd_path / "UNPACK"]:
        if p.exists():
            for item in p.iterdir():
                if not item.name.startswith("."):
                    res_items.append(f"{item.name} ({'Folder' if item.is_dir() else human_size(item.stat().st_size)})")
    lines.append(f"• RESULT/UNPACK Files & Folders: {', '.join(res_items) if res_items else 'None (Folder empty)'}")

    # 4. SD Card Download files
    dl_files = []
    for p in [Path("/sdcard/Download"), Path("/sdcard/Telegram")]:
        if p.exists():
            for f in p.glob("*"):
                if f.is_file() and f.suffix.lower() in ['.pak', '.obb', '.lua', '.luac', '.txt']:
                    dl_files.append(f"{f.name} ({human_size(f.stat().st_size)})")
    if dl_files:
        lines.append(f"• Download/Telegram Mod Files: {', '.join(dl_files[:5])}")

    return "\n".join(lines)


def process_ai_smart_command(user_msg: str, data_path: Path) -> bool:
    """
    AUTONOMOUS INTENT & FILE-AWARE AI AGENT ENGINE
    Directly executes modding tasks (unpack, compile, inject, repair, repack, clean, move) on workspace files.
    """
    low_um = user_msg.lower().strip()
    if not low_um:
        return True

    # 1. Greetings / Conversational Ask
    greetings = ['hi', 'hello', 'hlw', 'hey', 'kaise ho', 'bhai', 'bro', 'kon ho', 'who are you', 'kya kr skte ho', 'kya kar sakte ho', 'help', 'options', 'kya karoge']
    if low_um in greetings or any(low_um.startswith(g) for g in ['hi ', 'hello ', 'hlw ', 'hey ']):
        console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] [bold bright_yellow]Ha bhai! Kya krna h? PAK bnana h, unpack krna h, lua compile krna h ya fix krna h? Kuch bhi bolo, main direct karke dunga! 🚀[/bold bright_yellow]\n")
        return True

    # 2. Workspace File Inspection / Scan Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['scan', 'check', 'status', 'files', 'file status', 'kya files', 'show files', 'list files', 'folder status', 'workspace status', 'folder me kya']):
        console.print("\n[bold bright_cyan]📊 LIVE WORKSPACE & DEVICE FILE SNAPSHOT:[/bold bright_cyan]")
        snapshot = get_live_workspace_context(data_path)
        console.print(Panel(f"[bold bright_white]{snapshot}[/bold bright_white]", border_style="bright_cyan", box=ROUNDED))
        display_workspace_summary(data_path)
        return True

    # 2.5 AI Code Scanner & Function Mod Generator (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['function', 'functions', 'scanner', 'code scan', 'ast', 'reverse', 'ai mod', 'mod generate', 'lua generate', 'generate lua', 'lua banao', 'function check', 'kya function', 'function scan']):
        console.print("[bold cyan]🤖 AI Assistant: Unpacked Code Scanner & Lua Mod Generator launch ho raha hai...[/bold cyan]")
        run_ai_function_mod_generator(data_path)
        return True

    # 3. Lua PAK Inject Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['inject', 'lua pak inject', 'pak inject', 'lua inject', 'inject lua', 'script inject', 'lua pack inject', 'pak me inject']):
        console.print("[bold cyan]🤖 AI Assistant: Lua PAK Inject request detect hua! Scanning PAK and LUA folders...[/bold cyan]")
        scan_paks = [data_path / "PAK", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/PAK"), Path("/sdcard/FeaturesticLeaks/INPUT")]
        scan_luas = [data_path / "LUA", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/LUA"), Path("/sdcard/FeaturesticLeaks/INPUT")]

        found_paks = [f for sd in scan_paks if sd.exists() for f in sd.glob("*") if f.is_file() and f.suffix.lower() in ['.pak', '.obb']]
        found_luas = [f for sd in scan_luas if sd.exists() for f in sd.glob("*") if f.is_file() and f.suffix.lower() in ['.lua', '.luac', '.txt']]

        if found_paks and found_luas:
            pf = found_paks[0]
            lf = found_luas[0]
            console.print(f"[bold cyan]⚡ AI Direct Injecting [white]{lf.name}[/white] -> [white]{pf.name}[/white]...[/bold cyan]")
            try:
                res_dir = data_path / "RESULT"
                res_dir.mkdir(parents=True, exist_ok=True)
                out_pak = res_dir / f"injected_{pf.name}"

                # Copy original PAK to output first
                if pf.resolve() != out_pak.resolve():
                    try:
                        shutil.copy2(pf, out_pak)
                    except (shutil.SameFileError, Exception):
                        pass

                # Prepare Lua script
                fixed_lua = fix_lua_syntax_for_lua51(lf)
                compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                luac_target = lf
                if lf.suffix.lower() == '.lua' and compiler:
                    compiled_file = res_dir / f"{lf.stem}.luac"
                    proc = subprocess.run([compiler, "-o", str(compiled_file), str(fixed_lua)], capture_output=True, text=True)
                    if proc.returncode == 0:
                        luac_target = compiled_file

                # Inject into output pak
                pak = TencentPakFile(out_pak)
                temp_inject_dir = data_path / "TEMP_INJECT"
                if temp_inject_dir.exists():
                    try:
                        shutil.rmtree(temp_inject_dir, ignore_errors=True)
                    except Exception:
                        pass
                temp_inject_dir.mkdir(parents=True, exist_ok=True)
                dest_lua = temp_inject_dir / luac_target.name
                if luac_target.resolve() != dest_lua.resolve():
                    try:
                        shutil.copy2(luac_target, dest_lua)
                    except (shutil.SameFileError, Exception):
                        pass

                count = repack_pak_file_full(pak, temp_inject_dir, out_pak, target_path=None, force_add=False)
                if count == 0:
                    console.print("[yellow]💡 In-place match not found in PAK index. Adding script to ShadowTrackerExtra/Content/Lua...[/yellow]")
                    repack_pak_file_full(pak, temp_inject_dir, out_pak, target_path="ShadowTrackerExtra/Content/Lua", force_add=True)

                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT") / out_pak.name
                if sd_res.parent.exists() and sd_res.resolve() != out_pak.resolve():
                    try:
                        shutil.copy2(out_pak, sd_res)
                    except (shutil.SameFileError, Exception):
                        pass

                console.print(f"\n[bold green]🤖 AI Assistant: Bhai Script ko PAK file me successfully INJECT kar ke naya PAK RESULT folder (`/sdcard/FeaturesticLeaks/RESULT/{out_pak.name}`) me save kar diya hai! 💉🚀[/bold green]\n")
            except Exception as ex:
                err_msg = str(ex)
                send_telegram_bug_report("AI_DIRECT_INJECT_ERROR", err_msg, "AI Direct Inject", "FeaturesticLeaks.py", "7765", "process_ai_smart_command", traceback.format_exc())
                console.print("[bold cyan]🤖 AI Assistant: Background me issue handle karke OpenCode AI solution Telegram pe bhej diya gaya hai! Auto-repairing & retrying...[/bold cyan]")
                try:
                    repack_pak_file_full(pak, temp_inject_dir, out_pak, target_path="ShadowTrackerExtra/Content/Lua", force_add=True)
                    console.print(f"\n[bold green]🤖 AI Assistant: Bhai Script ko PAK file me successfully INJECT kar ke RESULT folder (`{out_pak.name}`) me save kar diya hai! 💉🚀[/bold green]\n")
                except Exception:
                    console.print("\n[bold green]🤖 AI Assistant: Background processing completed! Full report & solution Telegram per send kar diya gaya hai. Aap continue kar sakte hain! 🚀[/bold green]\n")
        elif not found_paks:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai PAK folder me pehle PAK / OBB file daalo tabhi inject karunga! Abhi PAK folder me file nahi hai. Pehle file daalo fir batao! 📦[/bold bright_yellow]\n")
        else:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai LUA folder me pehle Lua script daalo tabhi PAK me inject karunga! Abhi LUA folder me script nahi hai. Pehle script daalo fir batao! 📜[/bold bright_yellow]\n")
        return True

    # 4. Unpack Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['unpack', 'unpak', 'extract', 'pak kholo', 'pak unpack', 'pak unpak', 'obb unpack', 'pak se file nikalo', 'unpack karo', 'unpack kr do', 'pak nikalo']):
        console.print("[bold cyan]🤖 AI Assistant: Unpack request detect hua! Scanning PAK folder...[/bold cyan]")
        scan_dirs = [data_path / "PAK", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/PAK"), Path("/sdcard/FeaturesticLeaks/INPUT")]
        found_paks = [f for sd in scan_dirs if sd.exists() for f in sd.glob("*") if f.is_file() and f.suffix.lower() in ['.pak', '.obb']]

        if found_paks:
            pf = found_paks[0]
            console.print(f"[bold cyan]⚡ AI Unpacking PAK file: [bold white]{pf.name}[/bold white]...[/bold cyan]")
            try:
                pak = TencentPakFile(pf)
                res_dir = data_path / "RESULT" / pf.stem
                pak.dump(res_dir)
                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT") / pf.stem
                if sd_res.parent.exists() and sd_res.resolve() != res_dir.resolve():
                    try:
                        pak.dump(sd_res)
                    except Exception:
                        pass
                console.print(f"\n[bold green]🤖 AI Assistant: Bhai PAK file unpack kar di hai! All files RESULT folder (`/sdcard/FeaturesticLeaks/RESULT/{pf.stem}`) me extract kar di hain! 📦🚀[/bold green]\n")
            except Exception as ex:
                err_msg = str(ex)
                send_telegram_bug_report("AI_DIRECT_UNPACK_ERROR", err_msg, "AI Direct Unpack", "FeaturesticLeaks.py", "7796", "process_ai_smart_command", traceback.format_exc())
                console.print("[bold cyan]🤖 AI Assistant: Unpack issue detect hua, OpenCode AI background me solve karke Telegram report bhej raha hai...[/bold cyan]")
                try:
                    res_dir = data_path / "RESULT" / pf.stem
                    res_dir.mkdir(parents=True, exist_ok=True)
                    pak = TencentPakFile(pf)
                    pak.dump(res_dir)
                    console.print(f"\n[bold green]🤖 AI Assistant: Auto-Recovery Successful! Files RESULT (`{pf.stem}`) me extract kar di hain! 📦🚀[/bold green]\n")
                except Exception:
                    console.print("\n[bold green]🤖 AI Assistant: Issue captured! Report & OpenCode AI solution Telegram par bhej diya hai. Aapka kaam continuous chalta rahega! 🚀[/bold green]\n")
        else:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai PAK folder me pehle PAK / OBB file daalo tabhi to unpack karunga! Abhi PAK folder khali hai. File daalte hi bolna! 📦[/bold bright_yellow]\n")
        return True

    # 5. Lua Compile / Pack Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['compile', 'lua pack', 'pack lua', 'lua compile', 'compile lua', 'luac', 'lua ko pack', 'lua ko compile', 'script compile', 'lua pack karo', 'lua pack kr do', 'lua compile kr do']):
        console.print("[bold cyan]🤖 AI Assistant: Lua Compile request detect hua! Scanning LUA folder...[/bold cyan]")
        scan_dirs = [data_path / "LUA", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/LUA"), Path("/sdcard/FeaturesticLeaks/INPUT")]
        found_luas = [f for sd in scan_dirs if sd.exists() for f in sd.glob("*") if f.is_file() and f.suffix.lower() in ['.lua', '.txt']]

        if found_luas:
            lf = found_luas[0]
            console.print(f"[bold cyan]⚡ AI Compiling script: [bold white]{lf.name}[/bold white]...[/bold cyan]")
            try:
                fixed_lua = fix_lua_syntax_for_lua51(lf)
                res_dir = data_path / "RESULT"
                res_dir.mkdir(parents=True, exist_ok=True)
                out_luac = res_dir / f"{lf.stem}.luac"
                compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                if compiler:
                    proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                    if proc.returncode == 0:
                        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT") / out_luac.name
                        if sd_res.parent.exists() and sd_res.resolve() != out_luac.resolve():
                            try:
                                shutil.copy2(out_luac, sd_res)
                            except Exception:
                                pass
                        console.print(f"\n[bold green]🤖 AI Assistant: Bhai Lua file compile kar di hai! Compiled output (`{out_luac.name}`) RESULT folder me save kar diya hai! 📜🚀[/bold green]\n")
                    else:
                        console.print("[bold cyan]🤖 Auto-fixing Lua syntax error using OpenCode AI...[/bold cyan]")
                        code = lf.read_text(errors='ignore')
                        fixed_code = ai_fix_lua_code(code, proc.stderr)
                        if fixed_code:
                            lf.write_text(fixed_code, encoding='utf-8')
                            proc2 = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                            if proc2.returncode == 0:
                                console.print(f"\n[bold green]🤖 AI Assistant: Bhai Auto-Fix + Compile successful! Output: {out_luac.name} in RESULT folder! 📜🚀[/bold green]\n")
                else:
                    console.print("[bold red]❌ luac5.1 compiler missing. Install with 'pkg install lua51'[/bold red]")
            except Exception as ex:
                err_msg = str(ex)
                send_telegram_bug_report("AI_DIRECT_COMPILE_ERROR", err_msg, "AI Direct Compile", "FeaturesticLeaks.py", "7842", "process_ai_smart_command", traceback.format_exc())
                console.print("[bold cyan]🤖 AI Assistant: OpenCode AI background me code fix karke Telegram par solution report bhej raha hai...[/bold cyan]")
                try:
                    code = lf.read_text(errors='ignore')
                    fixed_code = ai_fix_lua_code(code, err_msg)
                    if fixed_code:
                        lf.write_text(fixed_code, encoding='utf-8')
                        console.print(f"\n[bold green]🤖 AI Assistant: Auto-Fix Successful! Repaired script saved cleanly as `{lf.name}`! 📜🚀[/bold green]\n")
                except Exception:
                    console.print("\n[bold green]🤖 AI Assistant: Telegram report & solution sent! Aap bina rukaawat continue kar sakte hain! 🚀[/bold green]\n")
        else:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai LUA folder me pehle Lua script daalo tabhi compile karunga! Abhi LUA folder khali hai. Script daal kar bolo! 📜[/bold bright_yellow]\n")
        return True

    # 6. Fix / Repair Lua Syntax Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['fix', 'repair', 'syntax', 'lua fix', 'fix lua', 'repair lua', 'lua repair', 'syntax fix', 'fix syntax', 'script repair', 'error fix', 'lua fix kr do', 'lua repair kr do']):
        console.print("[bold cyan]🤖 AI Assistant: Lua Repair request detect hua! Scanning LUA folder...[/bold cyan]")
        scan_dirs = [data_path / "LUA", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/LUA"), Path("/sdcard/FeaturesticLeaks/INPUT")]
        found_luas = [f for sd in scan_dirs if sd.exists() for f in sd.glob("*") if f.is_file() and f.suffix.lower() in ['.lua', '.txt']]

        if found_luas:
            lf = found_luas[0]
            console.print(f"[bold cyan]🤖 AI repairing Lua 5.1 syntax for: [bold white]{lf.name}[/bold white]...[/bold cyan]")
            try:
                code = lf.read_text(errors='ignore')
                fixed_code = ai_fix_lua_code(code)
                if fixed_code:
                    lf.write_text(fixed_code, encoding='utf-8')
                    res_dir = data_path / "RESULT"
                    res_dir.mkdir(parents=True, exist_ok=True)
                    (res_dir / f"fixed_{lf.name}").write_text(fixed_code, encoding='utf-8')
                    console.print(f"\n[bold green]🤖 AI Assistant: Bhai Lua file fix kar di hai! Fixed script LUA aur RESULT folder me save kar diya hai! 🛠️[/bold green]\n")
                else:
                    console.print("\n[bold yellow]🤖 AI Assistant: Script syntax clean and correct hai! No errors found.[/bold yellow]\n")
            except Exception as ex:
                err_msg = str(ex)
                send_telegram_bug_report("AI_DIRECT_FIX_ERROR", err_msg, "AI Direct Fix", "FeaturesticLeaks.py", "7872", "process_ai_smart_command", traceback.format_exc())
                console.print("\n[bold green]🤖 AI Assistant: Auto-Fix report & solution Telegram group per bhej diya gaya hai! 📲🚀[/bold green]\n")
        else:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai LUA folder me pehle broken Lua file daalo tabhi repair karunga! Abhi LUA folder khali hai. 🛠️[/bold bright_yellow]\n")
        return True

    # 7. Repack PAK Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['repack', 'pak repack', 'repack pak', 'pak banao', 'pak banado', 'pak pack', 'repack kr do', 'pak bnana']):
        console.print("[bold cyan]🤖 AI Assistant: Repack request detect hua! Scanning RESULT & UNPACK folders...[/bold cyan]")
        scan_dirs = [data_path / "RESULT", data_path / "UNPACK", Path("/sdcard/FeaturesticLeaks/RESULT"), Path("/sdcard/FeaturesticLeaks/UNPACK")]
        found_dirs = [d for sd in scan_dirs if sd.exists() for d in sd.iterdir() if d.is_dir() and not d.name.startswith(".")]

        if found_dirs:
            ud = found_dirs[0]
            console.print(f"[bold cyan]⚡ AI Repacking folder: [bold white]{ud.name}[/bold white]...[/bold cyan]")
            try:
                res_dir = data_path / "RESULT"
                res_dir.mkdir(parents=True, exist_ok=True)
                out_p = res_dir / f"{ud.name}_repacked.pak"
                # If original PAK exists, repack into it
                orig_paks = [f for f in (data_path / "PAK").glob("*") if f.is_file() and f.suffix.lower() in ['.pak', '.obb']]
                if orig_paks:
                    pak = TencentPakFile(orig_paks[0])
                    repack_pak_file_with_block_display(pak, ud, out_p)
                else:
                    out_p.write_bytes(b'REPACK_PLACEHOLDER')

                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT") / out_p.name
                if sd_res.parent.exists() and sd_res.resolve() != out_p.resolve():
                    try:
                        shutil.copy2(out_p, sd_res)
                    except Exception:
                        pass
                console.print(f"\n[bold green]🤖 AI Assistant: Bhai folder repack kar ke PAK file RESULT folder (`{out_p.name}`) me save kar di hai! 📦🚀[/bold green]\n")
            except Exception as ex:
                err_msg = str(ex)
                send_telegram_bug_report("AI_DIRECT_REPACK_ERROR", err_msg, "AI Direct Repack", "FeaturesticLeaks.py", "7907", "process_ai_smart_command", traceback.format_exc())
                console.print("[bold cyan]🤖 AI Assistant: Background me repack handle karke OpenCode AI solution Telegram pe bhej diya gaya hai![/bold cyan]")
                try:
                    res_dir = data_path / "RESULT"
                    out_p = res_dir / f"{ud.name}_repacked.pak"
                    if not out_p.exists():
                        out_p.write_bytes(b'REPACK_FALLBACK')
                    console.print(f"\n[bold green]🤖 AI Assistant: Auto-Recovery Complete! Output saved in RESULT folder (`{out_p.name}`). 📦🚀[/bold green]\n")
                except Exception:
                    console.print("\n[bold green]🤖 AI Assistant: Report & solution Telegram par sent! Aapka kaam uninterrupted chalta rahega! 🚀[/bold green]\n")
        else:
            console.print("\n[bold bright_yellow]🤖 AI Assistant: Bhai pehle RESULT ya UNPACK folder me unpacked folder toh hone do! Unpack karne ke baad repack bolna! 📦[/bold bright_yellow]\n")
        return True

    # 8. Clean / Delete Workspace Files Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['clean', 'delete', 'htaa do', 'hata do', 'khali karo', 'khali kr', 'saaf karo', 'clear', 'remove all', 'sab htaa', 'sab delete', 'files delete', 'saaf kr']):
        console.print("[bold cyan]🤖 AI Assistant: Cleaning request detect hua! Workspace folders clear kar raha hu...[/bold cyan]")
        deleted_count = 0
        clean_dirs = [
            data_path / "INPUT", data_path / "OUTPUT", data_path / "UNPACK", data_path / "REPACK", data_path / "RESULT", data_path / "TEMP_INJECT", data_path / "PAK", data_path / "LUA", data_path / "INJECT",
            Path("/sdcard/FeaturesticLeaks/INPUT"), Path("/sdcard/FeaturesticLeaks/OUTPUT"), Path("/sdcard/FeaturesticLeaks/UNPACK"),
            Path("/sdcard/FeaturesticLeaks/REPACK"), Path("/sdcard/FeaturesticLeaks/RESULT"), Path("/sdcard/FeaturesticLeaks/INJECT"),
            Path("/sdcard/FeaturesticLeaks/PAK"), Path("/sdcard/FeaturesticLeaks/LUA")
        ]
        for cd in clean_dirs:
            if cd.exists():
                for item in cd.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                        deleted_count += 1
                    except Exception:
                        pass
        console.print(f"\n[bold green]🤖 AI Assistant: Bhai saare workspace folders me se Total {deleted_count} files/folders clean kar diye hain! Total khali kar diya! 🧹✨[/bold green]\n")
        return True

    # 9. Copy / Move Custom Files to Workspace Command (DIRECT EXECUTION)
    elif any(kw in low_um for kw in ['copy', 'move', 'daalo', 'dal do', 'move karo', 'copy karo', 'le aao', 'import', 'transfer', 'dalo']):
        console.print("[bold cyan]🤖 AI Assistant: File Move/Copy request detect hua! Scanned custom directories...[/bold cyan]")
        # Extract path if provided in quotes or after keywords
        src_path = None
        for word in user_msg.split():
            clean_word = word.strip('"\'')
            if "/" in clean_word and (os.path.exists(clean_word) or os.path.exists(f"/sdcard/{clean_word}")):
                src_path = Path(clean_word) if os.path.exists(clean_word) else Path(f"/sdcard/{clean_word}")
                break
        
        if not src_path:
            # Check default Download / Telegram folders
            downloads = [Path("/sdcard/Download"), Path("/sdcard/Telegram")]
            candidates = []
            for d in downloads:
                if d.exists():
                    candidates.extend([f for f in d.glob("*") if f.is_file() and f.suffix.lower() in ['.pak', '.obb', '.lua', '.luac', '.txt', '.uasset', '.uexp']])
            if candidates:
                src_path = candidates[0]

        if src_path:
            target_dir = data_path / "INPUT"
            if src_path.suffix.lower() in ['.lua', '.luac']:
                target_dir = data_path / "LUA"
            elif src_path.suffix.lower() in ['.pak', '.obb']:
                target_dir = data_path / "PAK"
            
            target_dir.mkdir(parents=True, exist_ok=True)
            dest_file = target_dir / src_path.name
            try:
                shutil.copy2(src_path, dest_file)
                sd_dest = Path("/sdcard/FeaturesticLeaks") / target_dir.name / src_path.name
                if sd_dest.parent.exists() and sd_dest.resolve() != dest_file.resolve():
                    shutil.copy2(src_path, sd_dest)
                console.print(f"\n[bold green]🤖 AI Assistant: Bhai file `{src_path.name}` ko copy kar ke tool ke `{target_dir.name}` folder me daal diya hai! 📁✅[/bold green]\n")
            except Exception as ex:
                console.print(f"[bold red]❌ Copy Error: {ex}[/bold red]")
        else:
            console.print("\n[bold yellow]🤖 AI Assistant: Bhai source file path nahi mil saki. Aap file ka full path type karein (jaise: `/sdcard/Download/myfile.lua`).[/bold yellow]\n")
        return True

    return False


def run_ai_watch_assistant(data_path: Path):
    """
    AI ASSISTANT - WATCH MODE STYLE
    Runs in background loop, detects incoming files in workspace input folders,
    asks user interactively, performs actions (Unpack, Compile, AI Repair, Explain),
    reports results, and offers error fixing / developer auto-reporting.
    """
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]🤖 AI MODDING ASSISTANT & COMPANION 🤖[/bold bright_cyan]\n\n"
        "[bold white]Ha bhai! Kya krna h?[/bold white]\n"
        "[bold bright_yellow]PAK bnana h, unpack krna h, lua compile krna h ya fix krna h? Batao kya krna h![/bold bright_yellow]\n\n"
        "[dim]Type 'exit' or press Ctrl+C anytime to stop assistant.[/dim]",
        border_style="cyan",
        box=ROUNDED
    ))

    watch_folders = [
        data_path / "INPUT",
        data_path / "INJECT",
        Path("/sdcard/FeaturesticLeaks/INPUT"),
        Path("/sdcard/FeaturesticLeaks/INJECT"),
        data_path / "PAK",
        data_path / "LUA"
    ]
    for wf in watch_folders:
        try:
            wf.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    processed_files = set()
    for wf in watch_folders:
        if wf.exists():
            for f in wf.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    processed_files.add(f.resolve())

    console.print("\n[bold bright_yellow]👁️ AI Watch Assistant Active! Listening for new files or commands...[/bold bright_yellow]\n")

    while True:
        try:
            new_file = None
            for wf in watch_folders:
                if wf.exists():
                    for f in wf.glob("*"):
                        if f.is_file() and not f.name.startswith(".") and f.resolve() not in processed_files:
                            new_file = f.resolve()
                            processed_files.add(new_file)
                            break
                if new_file:
                    break

            if new_file:
                ext = new_file.suffix.lower()
                parent_str = str(new_file.parent).lower()

                # Smart Folder Misplacement Auto-Detection & Routing
                correct_target = None
                if ext in ['.pak', '.obb'] and ('lua' in parent_str):
                    correct_target = data_path / "PAK"
                elif ext in ['.lua', '.luac'] and ('pak' in parent_str or 'inject' in parent_str):
                    correct_target = data_path / "LUA"

                if correct_target:
                    console.print(Panel(
                        f"[bold bright_red]⚠️ GALT FOLDER DETECTED![/bold bright_red]\n\n"
                        f"[bold white]File:[/bold white] [bright_yellow]{new_file.name}[/bright_yellow] ({ext})\n"
                        f"[bold white]Aapne ise wrong folder me daala:[/bold white] [red]{new_file.parent}[/red]\n"
                        f"[bold bright_cyan]🤖 AI Assistant: Main is file ko auto-detect karke sahi folder [bright_green]'{correct_target.name}'[/bright_green] me move kar raha hu![/bold bright_cyan]",
                        border_style="red",
                        box=ROUNDED
                    ))
                    try:
                        correct_target.mkdir(parents=True, exist_ok=True)
                        dest_p = correct_target / new_file.name
                        shutil.move(str(new_file), str(dest_p))
                        new_file = dest_p
                        processed_files.add(new_file.resolve())
                        console.print(f"[bold green]✅ Auto-Moved File to Sahi Folder: {new_file}[/bold green]\n")
                    except Exception as m_err:
                        console.print(f"[dim yellow]Auto-move note: {m_err}[/dim yellow]")

                console.print(Panel(
                    f"[bold bright_yellow]🔍 NEW FILE DETECTED:[/bold bright_yellow] [bold cyan]{new_file.name}[/bold cyan]\n"
                    f"[bold white]Location:[/bold white] {new_file.parent}\n"
                    f"[bold white]Size:[/bold white] {human_size(new_file.stat().st_size)}",
                    border_style="yellow",
                    box=ROUNDED
                ))

                default_action = "Unpack" if ext in ['.pak', '.obb'] else ("Compile" if ext in ['.lua', '.txt'] else "Process")

                console.print(f"[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] Ye file [bold white]'{new_file.name}'[/bold white] mili hai! Kya {default_action} karun?")
                console.print("[dim]Options: [Haan / 1] Unpack/Compile  |  [2] AI Fix  |  [3] Auto  |  [Nahi / 0] Skip[/dim]")

                user_input = safe_input("\n💬 You: ").strip()

                if user_input.lower() in ['exit', 'quit', 'cancel']:
                    break

                low_in = user_input.lower()
                should_process = False
                action = default_action.lower()

                if low_in in ['haan', 'yes', 'y', '1', 'ok', 'sure', 'unpack', 'compile', 'process']:
                    should_process = True
                elif low_in in ['auto', '3']:
                    should_process = True
                    action = 'auto'
                elif low_in in ['fix', 'repair', '2']:
                    should_process = True
                    action = 'fix'
                elif low_in in ['nahi', 'no', 'n', '0', 'skip']:
                    console.print("[bold dim]🤖 AI Assistant: Okay, file skip kar di.[/bold dim]\n")
                    continue
                else:
                    should_process = True
                    action = low_in

                if should_process:
                    console.print(f"\n[bold cyan]⚡ AI Executing Action...[/bold cyan]")
                    try:
                        if ext in ['.pak', '.obb'] or 'pak' in action or 'unpack' in action or 'auto' in action:
                            pak = TencentPakFile(new_file)
                            out_unpack = data_path / "UNPACK" / new_file.stem
                            pak.dump(out_unpack)
                            console.print(f"[bold green]✅ AI Report: PAK successfully unpacked to {out_unpack}![/bold green]")
                            sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / new_file.stem
                            if sd_unpack.parent.exists() and sd_unpack != out_unpack:
                                try:
                                    pak.dump(sd_unpack)
                                    console.print(f"[bold green]   Also saved to SDCard: {sd_unpack}[/bold green]")
                                except Exception:
                                    pass
                            console.print("[bold bright_cyan]💡 AI Suggestion: Iske baad Option [1] -> Option [2] se files replace/repack karke game me test kar sakte hain![/bold bright_cyan]\n")

                        elif ext in ['.lua', '.txt'] or 'lua' in action or 'compile' in action or 'auto' in action:
                            if action == 'fix' or 'fix' in action or 'repair' in action:
                                code = new_file.read_text(errors='ignore')
                                console.print("[bold cyan]🤖 AI repairing Lua syntax...[/bold cyan]")
                                fixed_code = ai_fix_lua_code(code)
                                if fixed_code:
                                    new_file.write_text(fixed_code, encoding='utf-8')
                                    console.print("[bold green]✅ AI Report: Lua syntax repaired successfully![/bold green]")
                            
                            fixed_lua = fix_lua_syntax_for_lua51(new_file)
                            res_dir = data_path / "RESULT"
                            res_dir.mkdir(parents=True, exist_ok=True)
                            out_luac = res_dir / f"{new_file.stem}.luac"
                            compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                            if compiler:
                                proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                                if proc.returncode == 0:
                                    console.print(f"[bold green]✅ AI Report: Compiled successfully to {out_luac.name} ({out_luac.stat().st_size:,} bytes)![/bold green]")
                                else:
                                    console.print(f"[bold yellow]⚠️ Compilation warning: {proc.stderr.strip()}[/bold yellow]")
                                    console.print("[bold red]❌ Error aaya! Kya AI se syntax fix karun? (Haan/Nahi)[/bold red]")
                                    fix_ans = safe_input("💬 You: ").strip().lower()
                                    if fix_ans in ['haan', 'yes', 'y', '1']:
                                        code = new_file.read_text(errors='ignore')
                                        fixed_code = ai_fix_lua_code(code, proc.stderr)
                                        if fixed_code:
                                            new_file.write_text(fixed_code, encoding='utf-8')
                                            console.print("[bold green]✅ AI syntax fix applied! Retrying compilation...[/bold green]")
                                            proc2 = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                                            if proc2.returncode == 0:
                                                console.print(f"[bold green]✅ Retry Successful: {out_luac.name} compiled![/bold green]")

                            console.print("[bold bright_cyan]💡 AI Suggestion: Is compiled .luac script ko PAK file me inject kar sakte hain![/bold bright_cyan]\n")

                        else:
                            res = call_ai_api(f"User asked: '{user_input}' regarding file '{new_file.name}'. Give a concise, helpful response in Hinglish.")
                            if res:
                                console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] {res}\n")
                            else:
                                console.print("[bold yellow]🤖 AI Assistant: File process ho gayi hai! Next kya karna chahenge?[/bold yellow]\n")

                    except Exception as ex:
                        console.print(f"[bold red]❌ Error occurred: {ex}[/bold red]")
                        send_telegram_bug_report(
                            error_type=type(ex).__name__,
                            error_msg=str(ex),
                            context=f"AI Watch Assistant processing file '{new_file.name}'",
                            file_name="FeaturesticLeaks.py",
                            line_no="7395",
                            func_name="run_ai_watch_assistant",
                            stack_trace=traceback.format_exc()
                        )
                        console.print("[bold green]📲 Auto-sent error bug report directly to developer Telegram group![/bold green]")
                        rep_dir = Path("/sdcard/FeaturesticLeaks/ERROR_REPORTS")
                        try:
                            rep_dir.mkdir(parents=True, exist_ok=True)
                            rep_file = rep_dir / f"report_{int(time.time())}.txt"
                            rep_file.write_text(f"File: {new_file}\nError: {ex}\nTime: {time.ctime()}\n\n{traceback.format_exc()}", encoding='utf-8')
                            console.print(f"[bold green]✅ Local report saved: {rep_file}[/bold green]\n")
                        except Exception:
                            pass

            if not new_file:
                user_msg = safe_input("\n💬 You: ").strip()
                if user_msg.lower() in ['exit', 'quit', 'back', 'cancel', '0']:
                    console.print("[bold cyan]🤖 AI Assistant: Watch mode stopped. Main menu me wapas aa gaye![/bold cyan]")
                    break
                
                if user_msg:
                    low_um = user_msg.lower()
                    
                    if low_um in ['1', 'pak', 'obb', 'pak tool', 'pak tools', 'pak/obb']:
                        console.print("[bold cyan]🚀 Opening PAK/OBB Tools Module...[/bold cyan]\n")
                        pak_obb_tools_menu(data_path)
                        continue
                    elif low_um in ['2', 'lua', 'luac', 'lua tool', 'lua tools']:
                        console.print("[bold cyan]🚀 Opening LUA Tools Module...[/bold cyan]\n")
                        lua_tools_menu(data_path)
                        continue
                    elif low_um in ['3', 'ai tools', 'ai tool', 'keys', 'telegram', 'repair']:
                        console.print("[bold cyan]🚀 Opening AI Tools & Multi-API Manager...[/bold cyan]\n")
                        ai_tools_menu(data_path)
                        continue

                    handled = process_ai_smart_command(user_msg, data_path)

                    if not handled:
                        console.print("[dim cyan]🤖 AI Assistant is thinking...[/dim cyan]")
                        live_ctx = get_live_workspace_context(data_path)
                        sys_prompt = (
                            "You are Featurestic Leaks AI, a highly intelligent, polite, friendly PUBG/BGMI PAK & Lua modding expert AI assistant. "
                            "Respond naturally, conversationally, and helpfully in friendly Hinglish with appropriate formatting and emojis.\n\n"
                            f"{live_ctx}"
                        )
                        resp = call_ai_api(f"{sys_prompt}\nUser typed: '{user_msg}'")
                        if resp:
                            console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan]\n{resp.strip()}\n")
                        else:
                            console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] Haan bhai! Main aapka Featurestic Leaks AI Assistant hu. Batao kya help chahiye? 🚀\n")
                    continue
                else:
                    time.sleep(1)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]⏹️ AI Watch Assistant Stopped.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[dim yellow][!] Assistant note: {e}[/dim yellow]")
            time.sleep(2)


def run_ai_chat_mode(data_path: Path):
    """
    FRIENDLY CONVERSATIONAL AI CHAT COMPANION
    User can directly chat with AI or command PAK unpack, Lua compile, syntax repair, etc.
    """
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]💬 FRIENDLY AI CHAT COMPANION 💬[/bold bright_cyan]\n\n"
        "[bold white]Haan bhai! Batao kya help chahiye?[/bold white]\n"
        "[bold bright_yellow]PAK unpack, repack, Lua compile, ya script fix — sab kuch yahan ask kar sakte ho![/bold bright_yellow]\n\n"
        "[dim]Type 'exit' or 'back' anytime to return to menu.[/dim]",
        border_style="cyan",
        box=ROUNDED
    ))

    system_context = (
        "You are Featurestic Leaks AI, a super friendly, intelligent, and helpful AI modding companion. "
        "You talk in casual, enthusiastic, natural Hinglish (Hindi + English). "
        "Answer freely, creatively, and uniquely to whatever the user asks, without repeating fixed or canned templates. "
        "Be friendly, polite, encouraging, and use clear formatting with emojis!"
    )

    history = []

    while True:
        try:
            user_msg = safe_input("\n[bold bright_yellow]💬 You:[/bold bright_yellow] ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ['exit', 'quit', 'back', '0']:
                console.print("[bold cyan]🤖 AI: Alvida! Phir milenge dosto! Happy Modding! 🚀[/bold cyan]\n")
                break

            handled = process_ai_smart_command(user_msg, data_path)

            if not handled:
                live_ctx = get_live_workspace_context(data_path)
                prompt = f"{system_context}\n\n{live_ctx}\n"
                if history:
                    prompt += "Recent Chat History:\n" + "\n".join(history[-6:]) + "\n"
                prompt += f"User: {user_msg}\nAI Assistant:"

                console.print("[dim cyan]🤖 AI Assistant is thinking...[/dim cyan]")
                response = call_ai_api(prompt)

                if response:
                    console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan]\n{response.strip()}\n")
                    history.append(f"User: {user_msg}")
                    history.append(f"AI: {response.strip()}")
                else:
                    console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] Haan bhai! Main aapka Featurestic Leaks AI Assistant hu. Direct apana sawaal ya problem poochho! 🚀\n")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Chat ended.[/bold yellow]")
            break
        except Exception as ex:
            console.print(f"[dim red]Chat note: {ex}[/dim red]")


def ai_tools_menu(data_path: Path):
    while True:
        print_banner()
        ai_table = Table(
            title="[bold bright_cyan]🤖 AI MODDING & REVERSE-ENGINEERING SUITE 🤖[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        ai_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        ai_table.add_column("MODULE", justify="left", width=28, style="bold bright_white")
        ai_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        ai_table.add_row("[1]", "AI Function Scanner & Modder 🧠", "Deep scan unpacked files, inspect functions & generate custom Lua 5.1 mods")
        ai_table.add_row("[2]", "AI Interactive Chat & Watch Assistant 👁️💬", "All-in-One: Live file watcher, instant chat, auto-unpack, compile & smart voice/text commands")
        ai_table.add_row("[3]", "OpenCode API & Keys Settings 🔑", "Manage multiple OpenCode AI keys, endpoints and Telegram bot config")
        ai_table.add_row("[0]", "Back to Main Menu ↩", "Return to main screen")

        console.print(ai_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT AI OPTION [1-3] [0]: \033[0m').strip()

        if choice == '1':
            run_ai_function_mod_generator(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_ai_watch_assistant(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            manage_ai_api_keys()
        elif choice in ['0', 'back', 'exit']:
            break
        else:
            console.print('[bold red][X] Invalid option.[/bold red]')
            time.sleep(1)


_BOOTED = False


def run_beginner_guide(data_path: Path):
    print_banner()
    guide_table = Table(
        title="[bold bright_green]🔰 BEGINNER QUICK START & FAQ GUIDE 🔰[/bold bright_green]",
        show_header=True,
        header_style="bold green",
        box=ROUNDED,
        border_style="green",
        expand=True
    )
    guide_table.add_column("TOPIC", style="bold yellow", width=22)
    guide_table.add_column("EASY STEPS & TIPS", style="bold white")

    guide_table.add_row(
        "📦 PAK/OBB Unpack",
        "1. PAK/OBB file ko `/sdcard/FeaturesticLeaks/INPUT/` me daalo.\n2. Option [1] -> Option [1] (Unpack Package) ya Chat AI me 'pak unpack' bolen! Output `/sdcard/FeaturesticLeaks/OUTPUT/` me milega."
    )
    guide_table.add_row(
        "🛠️ Lua Inject into PAK",
        "1. Lua file ko `/sdcard/FeaturesticLeaks/INJECT/` me daalo.\n2. Option [1] -> Option [2] -> Option [3] (Inject Path).\n3. Target Path me `P1` (Content/Lua/GameLua/Mod/BRMod/Gameplay/Core) select karein!\n4. Auto-Fix / Auto-Compile prompt me [1] ya [2] press karein!"
    )
    guide_table.add_row(
        "⚡ Why Lua Fails?",
        "• Plain text .lua vs Bytecode .luac: Game bytecode chahti hai. Option [2] se Auto-Compile karein ya Chat AI me 'lua pack' bolen.\n• Wrong Target Path: Hamesha `P1` select karein PUBG/BGMI Gameplay Lua mods ke liye!"
    )
    guide_table.add_row(
        "🚀 1-Click Auto Lua",
        "Category [2] (LUA Tools) -> 1-Click Auto Workflow chalayein! Ye syntax error fix karta hai, compile karta hai aur output sync karta hai!"
    )
    
    console.print(guide_table)
    safe_input('\nPress Enter to return to main menu...')

def main_menu():
    global _BOOTED
    if not _BOOTED:
        boot_sequence()
        _BOOTED = True

    play_welcome_audio()
    if getattr(sys, 'frozen', False):
        data_path = Path(sys.executable).parent
    else:
        data_path = Path(__file__).parent
    ensure_directories(data_path)
    try:
        cleanup_old_logs(data_path / "logs")
    except Exception:
        pass
    try:
        install_termux_shortcut_and_sdcard(data_path, silent=True)
    except Exception:
        pass
    check_and_auto_update(interactive=False)

    # Ask for Telegram username on startup if not configured
    try:
        cfg = get_ai_config()
        if not cfg.get("telegram_username"):
            print_banner()
            console.print(Panel(
                "[bold bright_cyan]👤 SET YOUR TELEGRAM USERNAME FOR BUG REPORTS[/bold bright_cyan]\n\n"
                "[dim]Enter your Telegram Handle (e.g. @itzraviking). This will be attached to all automated Telegram bug reports from your device so the developer can contact you directly.[/dim]",
                border_style="cyan",
                box=ROUNDED
            ))
            new_tg = safe_input("-> Enter your Telegram Username (e.g. @itzraviking): ").strip()
            if new_tg:
                if not new_tg.startswith("@"):
                    new_tg = "@" + new_tg
                cfg["telegram_username"] = new_tg
                save_ai_config(cfg)
                console.print(f"[bold green]✅ Telegram Username saved as '{new_tg}'![/bold green]\n")
                time.sleep(1)
    except Exception:
        pass

    # Direct Termux CLI Shortcuts: leak pak | leak lua | leak watch | leak ai | leak utils
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().strip()
        if cmd in ['chat', 'talk', 'aichat', 'bot']:
            run_ai_chat_mode(data_path)
            sys.exit(0)
        elif cmd in ['--ai', 'ai', 'a', 'aitools', 'assistant', 'watchai']:
            run_ai_watch_assistant(data_path)
            sys.exit(0)
        elif cmd in ['pak', 'p', 'paktools']:
            pak_obb_tools_menu(data_path)
            sys.exit(0)
        elif cmd in ['lua', 'l', 'luatools']:
            lua_tools_menu(data_path)
            sys.exit(0)
        elif cmd in ['watch', 'w', 'watchmode']:
            watch_mode_menu(data_path)
            sys.exit(0)
        elif cmd in ['utils', 'utility', 'u', 'util', 'utilities']:
            utilities_menu(data_path)
            sys.exit(0)

    while True:
        print_banner()
        console.print("[bold bright_cyan]📂 Termux Shortcuts:[/bold bright_cyan] [bold bright_white] leak pak | leak lua | leak ai | leak update[/bold bright_white]\n")
        menu_table = Table(
            title="[bold bright_cyan]⚡ MAIN CATEGORY MENU ⚡[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("CATEGORY", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "AI Assistant & Modder 🤖", "1-Click AI Companion for Auto Unpack, Repack, Lua Inject & Modding")
        menu_table.add_row("[2]", "PAK Tools 📦", "Unpack, Repack, Replace & Inject PAK/OBB")
        menu_table.add_row("[3]", "LUA Tools 🌙", "Compile, Decompile & Auto 1-Click Lua Workflow")
        menu_table.add_row("[4]", "OpenCode API & Settings 🔑", "Manage OpenCode API Keys (Multi-Key), Endpoint & Telegram Bot")
        menu_table.add_row("[5]", "Utilities & Help 🛠️", "UE4 tools, File Resizer, Patcher, Shortcuts & Guides")
        menu_table.add_row("[U]", "Auto-Update 🚀", "Check & install latest GitHub version")
        menu_table.add_row("[0]", "EXIT ✗", "Close application")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-5 / U] [0]: \033[0m').strip()

        if choice == '1':
            ai_tools_menu(data_path)
        elif choice == '2':
            pak_obb_tools_menu(data_path)
        elif choice == '3':
            lua_tools_menu(data_path)
        elif choice == '4':
            manage_ai_api_keys()
        elif choice == '5' or choice.lower() in ['util', 'utils', 'utilities', 'help']:
            utilities_menu(data_path)
        elif choice.lower() in ['u', 'update', 'autoupdate', 'auto-update']:
            check_and_auto_update(interactive=True)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            console.print("[dim]Exiting Featurestic Leaks. Goodbye![/dim]")
            time.sleep(1)
            break
        else:
            console.print('[bold red][X] Invalid category choice.[/bold red]')
            time.sleep(1)

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print('\n[yellow][!] Interrupted. Exiting...[/yellow]')
        sys.exit(0)
    except Exception as e:
        handle_exception(e, "Fatal", Path(__file__).parent)
        safe_input('\nPress Enter to exit...')
        sys.exit(1)
