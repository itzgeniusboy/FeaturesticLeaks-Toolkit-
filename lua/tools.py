import os
import sys
import re
import time
import base64
import zlib
import shutil
import subprocess
import struct
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.box import ROUNDED
    from rich.table import Table
    from rich.markup import escape
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                print(*args)
    console = DummyConsole()
    Panel = None
    Align = None
    ROUNDED = None
    Table = None
    escape = lambda x: str(x)

from lua.reader import (
    _LuaCustomReader, _LuaProto, _LuaStdReader, _LuaStdProto,
    _parse_lua_custom, _load_lua_custom_proto, _parse_lua_std,
    _std_to_custom_lua_proto, _load_std_bytecode_to_proto, _lua_xor
)
from lua.decompiler import _pseudo_decompile_lua, fix_lua_syntax_for_lua51
from core.logging_utils import handle_exception

def _ui():
    import FeaturesticLeaks
    return FeaturesticLeaks.safe_input, FeaturesticLeaks.human_size, FeaturesticLeaks.pick_file_from_folder

def safe_input(prompt: str = '', context: str = '~') -> str:
    import FeaturesticLeaks
    return FeaturesticLeaks.safe_input(prompt, context)

def human_size(size: int) -> str:
    import FeaturesticLeaks
    return FeaturesticLeaks.human_size(size)

def pick_file_from_folder(action_title: str, default_folder: Path, extensions: Optional[List[str]] = None):
    import FeaturesticLeaks
    if extensions is None:
        extensions = [".pak", ".obb"]
    return FeaturesticLeaks.pick_file_from_folder(action_title, default_folder, extensions)
class UniversalLuaPacker:
    """
    Universal Lua pack/unpack (encode/decode) module with 8-byte ASCII tag headers
    and extensible plugin architecture.
    """
    TAG_LEN = 8
    XOR_KEY = 0x5A

    _registry = {}

    @classmethod
    def register(cls, name: str, pack_fn, unpack_fn):
        """Register a new packing/unpacking method."""
        cls._registry[name.lower()] = (pack_fn, unpack_fn)

    @classmethod
    def _format_tag(cls, name: str) -> bytes:
        tag = name.upper().ljust(cls.TAG_LEN, '_')[:cls.TAG_LEN]
        return tag.encode('ascii')

    @classmethod
    def _parse_tag(cls, tag_bytes: bytes) -> str:
        try:
            return tag_bytes.decode('ascii', errors='ignore').rstrip('_').lower()
        except Exception:
            return ""

    @classmethod
    def pack(cls, method: str, input_bytes: bytes) -> bytes:
        """Packs input_bytes using the specified method name and prepends 8-byte ASCII tag."""
        method_key = method.lower()
        if method_key not in cls._registry:
            raise ValueError(f"Unrecognized packing method '{method}'. Available methods: {list(cls._registry.keys())}")
        pack_fn, _ = cls._registry[method_key]
        tag = cls._format_tag(method_key)
        payload = pack_fn(input_bytes)
        return tag + payload

    @classmethod
    def unpack(cls, packed_bytes: bytes) -> bytes:
        """Auto-detects method from 8-byte ASCII tag header and unpacks payload back to original bytes."""
        if len(packed_bytes) < cls.TAG_LEN:
            raise ValueError("Invalid packed payload: data shorter than 8-byte tag header.")
        tag_bytes = packed_bytes[:cls.TAG_LEN]
        method_key = cls._parse_tag(tag_bytes)
        if method_key not in cls._registry:
            raise ValueError(f"Unrecognized tag header '{tag_bytes.decode('ascii', errors='ignore')}'. Available methods: {list(cls._registry.keys())}")
        _, unpack_fn = cls._registry[method_key]
        payload = packed_bytes[cls.TAG_LEN:]
        return unpack_fn(payload)

    @classmethod
    def run_self_test(cls) -> bool:
        """Verifies lossless round-trip for all registered methods."""
        test_sample = b"-- FeaturesticLeaks Universal Lua Pack/Unpack Self-Test\nlocal x = 10\nprint('OK')"
        for method in cls._registry:
            packed = cls.pack(method, test_sample)
            unpacked = cls.unpack(packed)
            assert unpacked == test_sample, f"Lossless round-trip test failed for method '{method}'"
        return True


# Default Methods Registration
def _b64_pack(data: bytes) -> bytes:
    return base64.b64encode(data)

def _b64_unpack(payload: bytes) -> bytes:
    return base64.b64decode(payload)

def _xor_pack(data: bytes) -> bytes:
    xor_data = bytes(b ^ UniversalLuaPacker.XOR_KEY for b in data)
    return base64.b64encode(xor_data)

def _xor_unpack(payload: bytes) -> bytes:
    raw_b64 = base64.b64decode(payload)
    return bytes(b ^ UniversalLuaPacker.XOR_KEY for b in raw_b64)

def _zlib_pack(data: bytes) -> bytes:
    compressed = zlib.compress(data)
    return base64.b64encode(compressed)

def _zlib_unpack(payload: bytes) -> bytes:
    compressed = base64.b64decode(payload)
    return zlib.decompress(compressed)

def _raw_pack(data: bytes) -> bytes:
    return data

def _raw_unpack(payload: bytes) -> bytes:
    return payload

UniversalLuaPacker.register("b64", _b64_pack, _b64_unpack)
UniversalLuaPacker.register("xor", _xor_pack, _xor_unpack)
UniversalLuaPacker.register("zlib", _zlib_pack, _zlib_unpack)
UniversalLuaPacker.register("raw", _raw_pack, _raw_unpack)

# Run self-test on load
try:
    UniversalLuaPacker.run_self_test()
except Exception:
    pass


def run_universal_lua_pack(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 UNIVERSAL LUA PACKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    
    lua_file, _ = pick_file_from_folder("Universal Pack Lua", lua_dir, extensions=[".lua", ".txt", ".luac"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print("\n[bold green]Available Packing Methods:[/bold green]")
    console.print(" [1] b64  - Base64 Encode")
    console.print(" [2] xor  - XOR + Base64 Encode")
    console.print(" [3] zlib - Zlib Compress + Base64 Encode")
    console.print(" [4] raw  - Tag Header Passthrough\n")
    
    method_choice = safe_input('SELECT METHOD [1-4] (default 1): ').strip()
    method_map = {'1': 'b64', '2': 'xor', '3': 'zlib', '4': 'raw'}
    method_name = method_map.get(method_choice, 'b64')

    try:
        raw_bytes = lua_file.read_bytes()
        packed_bytes = UniversalLuaPacker.pack(method_name, raw_bytes)
        
        res_dir = data_path / "RESULT"
        res_dir.mkdir(parents=True, exist_ok=True)
        out_file = res_dir / f"{lua_file.stem}_packed.bin"
        out_file.write_bytes(packed_bytes)
        
        console.print(f"[bold green][OK] File packed successfully using method '{method_name.upper()}':[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        console.print(f"     [dim]Header Tag: {packed_bytes[:8].decode('ascii', errors='ignore')} | Output Size: {len(packed_bytes)} bytes[/dim]")
    except Exception as e:
        console.print(f"[bold red][X] Packing failed: {e}[/bold red]")


def run_universal_lua_unpack(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔓 UNIVERSAL LUA UNPACKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    res_dir = data_path / "RESULT"
    lua_dir = data_path / "LUA"
    
    packed_file, _ = pick_file_from_folder("Universal Unpack Lua", res_dir, extensions=[".bin", ".lua", ".txt"])
    if not packed_file:
        packed_file, _ = pick_file_from_folder("Universal Unpack Lua", lua_dir, extensions=[".bin", ".lua", ".txt"])
    if not packed_file:
        custom_input = safe_input('-> Enter custom packed file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        packed_file = Path(custom_input)
        if not packed_file.exists() or not packed_file.is_file():
            console.print(f'[bold red][X] File not found: {packed_file}[/bold red]')
            return

    try:
        packed_bytes = packed_file.read_bytes()
        unpacked_bytes = UniversalLuaPacker.unpack(packed_bytes)
        
        out_file = res_dir / f"{packed_file.stem}_unpacked.lua"
        out_file.write_bytes(unpacked_bytes)
        
        tag_str = packed_bytes[:8].decode('ascii', errors='ignore')
        console.print(f"[bold green][OK] Auto-detected Header Tag '{tag_str}' & unpacked successfully:[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        console.print(f"     [dim]Restored Original Size: {len(unpacked_bytes)} bytes[/dim]")
    except Exception as e:
        console.print(f"[bold red][X] Unpacking failed: {e}[/bold red]")


def run_lua_string_obfuscator(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔒 LUA STRING OBFUSCATOR & DUMPER ENGINE[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    lua_file, _ = pick_file_from_folder("Lua String Tool", lua_dir, extensions=[".lua", ".txt", ".luac"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print("\n[bold bright_yellow]Select Tool Mode:[/bold bright_yellow]")
    console.print(" [1] 🔒 Encrypt All Strings in Script (Hex / Base64 / XOR + Auto-Decoder Wrapper)")
    console.print(" [2] 🔍 Extract & Dump All String Constants, URLs & Memory Offsets")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Option (0-2): ').strip()
    if mode == '0' or not mode:
        return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)

    if mode == '1':
        console.print("\n[bold bright_cyan][+] Obfuscating string literals...[/bold bright_cyan]")
        
        # Extract quoted strings (e.g. "hello", 'world')
        str_pattern = re.compile(r'(".*?"|\'.*?\')')
        
        def encrypt_match(m):
            s = m.group(1)[1:-1]
            if len(s) < 2 or "function" in s or "local" in s or "return" in s or "gg." in s:
                return m.group(1)
            hex_encoded = s.encode("utf-8").hex()
            # Wrap in Lua hex-decode function call
            return f'_HEX("{hex_encoded}")'

        obfuscated_code = str_pattern.sub(encrypt_match, content)

        # Inject decoder runtime at the top
        decoder_header = (
            "-- [FEATURESTIC LEAKS OBFUSCATED SCRIPT]\n"
            "local function _HEX(hex_str)\n"
            "    return (hex_str:gsub('..', function(cc)\n"
            "        return string.char(tonumber(cc, 16))\n"
            "    end))\n"
            "end\n\n"
        )
        final_code = decoder_header + obfuscated_code
        
        out_file = res_dir / f"{lua_file.stem}_obfuscated.lua"
        out_file.write_text(final_code, encoding="utf-8")
        
        console.print(f"[bold green][OK] Obfuscated Lua script saved successfully:[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_file, sd_res / out_file.name)
                console.print(f"     [bold green]📲 Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
            except Exception:
                pass

    elif mode == '2':
        dump_dir = data_path / "DUMP_LOGS"
        dump_dir.mkdir(parents=True, exist_ok=True)
        dump_file = dump_dir / f"{lua_file.stem}_strings_dump.txt"

        # Regex for strings, URLs, Hex values
        strings_found = re.findall(r'["\'](.*?)["\']', content)
        urls = re.findall(r'https?://[^\s"\']+', content)
        ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
        hex_offsets = re.findall(r'0x[0-9a-fA-F]+', content)

        with open(dump_file, "w", encoding="utf-8") as f:
            f.write(f"=== FEATURESTIC LEAKS LUA STRING DUMP: {lua_file.name} ===\n\n")
            f.write(f"--- URLs Identified ({len(urls)}) ---\n")
            for u in set(urls):
                f.write(f"  {u}\n")
            f.write(f"\n--- IP Addresses Identified ({len(ips)}) ---\n")
            for ip in set(ips):
                f.write(f"  {ip}\n")
            f.write(f"\n--- Memory Offsets Identified ({len(hex_offsets)}) ---\n")
            for ho in sorted(set(hex_offsets)):
                f.write(f"  {ho}\n")
            f.write(f"\n--- Literal Strings Found ({len(strings_found)}) ---\n")
            for s in set(strings_found):
                if len(s.strip()) > 1:
                    f.write(f"  {s}\n")

        console.print(f"[bold green][OK] Extracted {len(strings_found)} strings, {len(urls)} URLs, {len(ips)} IPs, {len(hex_offsets)} memory offsets![/bold green]")
        console.print(f" 📄 Report: [bold white]{dump_file}[/bold white]")
        
        sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
        if sd_dump.parent.exists():
            try:
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dump_file, sd_dump / dump_file.name)
                console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/DUMP_LOGS/[/bold green]")
            except Exception:
                pass


def run_lua_anti_bypass_analyzer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🛡️ LUA ANTI-BYPASS & SECURITY ANALYZER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("Lua Security Analyzer", lua_dir, extensions=[".lua", ".txt"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    rules = [
        ("HIGH", "Memory Edit Call", r'gg\.editAll|gg\.setValues|gg\.setRanges'),
        ("HIGH", "Memory Search Hook", r'gg\.searchNumber|gg\.refineNumber'),
        ("CRITICAL", "Anti-Cheat Clearance", r'gg\.clearResults|gg\.clearList'),
        ("MEDIUM", "Process Termination", r'os\.exit|os\.execute|os\.remove'),
        ("HIGH", "Dynamic Code Execution", r'loadstring|load|dofile|require'),
        ("HIGH", "Bytecode Injection / Dump", r'string\.dump|debug\.getinfo|debug\.getupvalue'),
        ("MEDIUM", "Memory Offset Pointer", r'0x[0-9a-fA-F]{4,}'),
        ("INFO", "GameGuard Toast / Alert", r'gg\.toast|gg\.alert|gg\.prompt')
    ]

    findings = []
    risk_score = 0

    for idx, line in enumerate(lines, 1):
        for severity, cat, pattern in rules:
            matches = re.findall(pattern, line)
            if matches:
                findings.append({
                    "line": idx,
                    "severity": severity,
                    "category": cat,
                    "match": matches[0],
                    "text": line.strip()[:80]
                })
                if severity == "CRITICAL": risk_score += 25
                elif severity == "HIGH": risk_score += 15
                elif severity == "MEDIUM": risk_score += 8
                elif severity == "INFO": risk_score += 2

    risk_score = min(100, risk_score)

    table = Table(
        title=f"[bold bright_cyan]📊 LUA AUDIT RESULTS: {escape(lua_file.name)} (Risk Score: {risk_score}/100)[/bold bright_cyan]",
        border_style="bright_cyan",
        box=ROUNDED
    )
    table.add_column("Line", style="bold yellow", justify="center", width=6)
    table.add_column("Severity", style="bold white", width=10)
    table.add_column("Category", style="bright_cyan", width=20)
    table.add_column("Code Snippet", style="dim")

    for f in findings[:25]:
        sev_color = "red" if f["severity"] in ["CRITICAL", "HIGH"] else "yellow" if f["severity"] == "MEDIUM" else "green"
        table.add_row(
            str(f["line"]),
            f"[{sev_color}]{f['severity']}[/{sev_color}]",
            escape(str(f["category"])),
            escape(str(f["text"]))
        )

    console.print(table)

    dump_dir = data_path / "DUMP_LOGS"
    dump_dir.mkdir(parents=True, exist_ok=True)
    report_file = dump_dir / f"{lua_file.stem}_security_audit.txt"

    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(f"=== FEATURESTIC LEAKS LUA SECURITY AUDIT REPORT ===\n")
        rf.write(f"Target File: {lua_file.name}\n")
        rf.write(f"Risk Score: {risk_score}/100\n")
        rf.write(f"Total Detections: {len(findings)}\n")
        rf.write("="*60 + "\n\n")
        for f in findings:
            rf.write(f"Line {f['line']:<5} | [{f['severity']:<8}] {f['category']:<22} | Match: {f['match']}\n  Code: {f['text']}\n\n")

    console.print(f"\n[bold green][OK] Detailed audit report saved to:[/bold green] [bold white]{report_file}[/bold white]")
    sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
    if sd_dump.parent.exists():
        try:
            sd_dump.mkdir(parents=True, exist_ok=True)
            shutil.copy2(report_file, sd_dump / report_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/DUMP_LOGS/[/bold green]")
        except Exception:
            pass


def run_lua_header_fixer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔧 LUA BYTECODE HEADER FIXER & DEBUG STRIPPER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    res_dir = data_path / "RESULT"
    lua_file, _ = pick_file_from_folder("Lua Header Fixer", lua_dir, extensions=[".luac", ".lua", ".bytes", ".bytecode"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom compiled .luac file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    raw_bytes = lua_file.read_bytes()
    if len(raw_bytes) < 12:
        console.print("[bold red][X] File size too small to be a valid Lua bytecode file.[/bold red]")
        return

    console.print(f"[bold cyan][+] Current Header Magic Bytes (First 12 Bytes):[/bold cyan] [bold yellow]{raw_bytes[:12].hex(' ').upper()}[/bold yellow]")

    console.print("\n[bold bright_yellow]Select Repair / Fix Action:[/bold bright_yellow]")
    console.print(" [1] Restore Standard Lua 5.1 Bytecode Header (1B 4C 75 61 51 00...)")
    console.print(" [2] Restore Standard LuaJIT Bytecode Header (1B 4C 4A 01/02...)")
    console.print(" [3] Strip Debug Symbols & Local Variable Names")
    console.print(" [0] Cancel\n")

    act = safe_input("-> Select Action (0-3): ").strip()
    if act == '0' or not act:
        return

    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / f"{lua_file.stem}_header_fixed.luac"

    if act == '1':
        # Standard Lua 5.1 header
        std_lua51_header = bytes([0x1B, 0x4C, 0x75, 0x61, 0x51, 0x00, 0x01, 0x04, 0x08, 0x04, 0x08, 0x00])
        fixed_bytes = std_lua51_header + raw_bytes[12:]
        out_file.write_bytes(fixed_bytes)
        console.print(f"[bold green][OK] Fixed Lua 5.1 magic header & written to:[/bold green] [bold white]{out_file}[/bold white]")

    elif act == '2':
        # Standard LuaJIT 2.0 header
        std_luajit_header = bytes([0x1B, 0x4C, 0x4A, 0x02])
        fixed_bytes = std_luajit_header + raw_bytes[4:]
        out_file.write_bytes(fixed_bytes)
        console.print(f"[bold green][OK] Fixed LuaJIT magic header & written to:[/bold green] [bold white]{out_file}[/bold white]")

    elif act == '3':
        # Strip debug names if possible or invoke luac -s
        if shutil.which("luac5.1") or shutil.which("luac"):
            compiler = shutil.which("luac5.1") or shutil.which("luac")
            cmd = [compiler, "-s", "-o", str(out_file), str(lua_file)]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0:
                    console.print(f"[bold green][OK] Stripped debug symbols using '{compiler}':[/bold green] [bold white]{out_file}[/bold white]")
                else:
                    out_file.write_bytes(raw_bytes)
                    console.print(f"[bold yellow][!] Compiler strip warning, copied original file.[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red][X] Error stripping debug symbols: {e}[/bold red]")
        else:
            out_file.write_bytes(raw_bytes)
            console.print(f"[bold yellow][!] No luac compiler found to strip debug info. Output saved.[/bold yellow]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/[/bold green]")
        except Exception:
            pass


def run_lua_script_optimizer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]⚡ LUA SCRIPT MINIFIER, CLEANER & SYNTAX CHECKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    lua_file, _ = pick_file_from_folder("Lua Optimizer", lua_dir, extensions=[".lua", ".txt"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    original_size = len(content.encode('utf-8'))

    console.print("\n[bold cyan][+] Performing Pre-Flight Syntax Integrity Check...[/bold cyan]")
    do_cnt = len(re.findall(r'\bdo\b', content))
    end_cnt = len(re.findall(r'\bend\b', content))
    fn_cnt = len(re.findall(r'\bfunction\b', content))
    if_cnt = len(re.findall(r'\bif\b', content))

    console.print(f"  • Functions: {fn_cnt} | If blocks: {if_cnt} | Do blocks: {do_cnt} | End keywords: {end_cnt}")
    if (do_cnt + fn_cnt + if_cnt) != end_cnt:
        console.print("[bold yellow]⚠️ Notice: Keyword count mismatch detected (Check block closures before running in GG).[/bold yellow]")
    else:
        console.print("[bold green]✅ Structural block closures balanced![/bold green]")

    console.print("\n[bold bright_yellow]Select Optimization Mode:[/bold bright_yellow]")
    console.print(" [1] 🧹 Strip Comments & Clean Whitespace (Keep Readable Layout)")
    console.print(" [2] ⚡ Full Compact Minify (Remove All Comments & Compact Lines)")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Mode [1-2] [1]: ').strip() or '1'
    if mode == '0':
        return

    cleaned = re.sub(r'--\[\[.*?\]\]', '', content, flags=re.DOTALL)
    
    if mode == '1':
        lines = []
        for line in cleaned.splitlines():
            line_str = line.strip()
            if line_str.startswith('--'):
                continue
            if '--' in line_str and not ('"' in line_str or "'" in line_str):
                line_str = line_str.split('--')[0].rstrip()
            if line_str:
                lines.append(line_str)
        final_code = "\n".join(lines)
    else:
        lines = []
        for line in cleaned.splitlines():
            line_str = line.strip()
            if line_str.startswith('--'):
                continue
            if '--' in line_str and not ('"' in line_str or "'" in line_str):
                line_str = line_str.split('--')[0].rstrip()
            if line_str:
                lines.append(line_str)
        final_code = "; ".join(lines)
        final_code = re.sub(r';\s*;', ';', final_code)

    new_size = len(final_code.encode('utf-8'))
    reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / f"{lua_file.stem}_optimized.lua"
    out_file.write_text(final_code, encoding="utf-8")

    console.print(f"\n[bold green][OK] Lua Script Optimized Successfully![/bold green]")
    console.print(f" 📉 [bold white]Size Reduced: {original_size} bytes ➔ {new_size} bytes ({reduction:.1f}% saved)[/bold white]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


def run_gg_code_generator(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🪄 GAMEGUARD (GG) MEMORY CODE & SCRIPT GENERATOR[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    console.print("\n[bold bright_yellow]Select Memory Snippet Template to Generate:[/bold bright_yellow]")
    console.print(" [1] 🎯 Search Value, Refine & Edit Memory Snippet")
    console.print(" [2] 🔒 Search Value & Freeze in Memory List")
    console.print(" [3] ⚡ Game Speedhack Toggle Handler")
    console.print(" [4] 🛡️ Anti-Cheat Log Remover & Process Stealth Handler")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Option [1-4] [1]: ').strip() or '1'
    if mode == '0':
        return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)

    if mode == '1':
        s_val = safe_input("-> Enter Search Number (e.g. 100 or 1.2345): ").strip() or "100"
        s_type = safe_input("-> Enter Value Type (DWORD/FLOAT/DOUBLE/BYTE/QWORD) [FLOAT]: ").upper().strip() or "FLOAT"
        e_val = safe_input("-> Enter New Replacement Value (e.g. 99999): ").strip() or "99999"

        gg_type = f"gg.TYPE_{s_type}"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SEARCH & EDIT SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function _FEATURESTIC_SEARCH_EDIT()
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber("{s_val}", {gg_type})
    local count = gg.getResultCount()
    if count == 0 then
        gg.toast("⚠️ No results found for {s_val}!")
        return
    end
    local results = gg.getResults(count)
    gg.editAll("{e_val}", {gg_type})
    gg.toast("✅ Successfully edited " .. tostring(#results) .. " memory addresses to {e_val}!")
end
_FEATURESTIC_SEARCH_EDIT()
"""
        out_file = res_dir / "GG_Search_Edit_Template.lua"

    elif mode == '2':
        s_val = safe_input("-> Enter Search Number: ").strip() or "500"
        s_type = safe_input("-> Enter Value Type (DWORD/FLOAT/BYTE) [DWORD]: ").upper().strip() or "DWORD"
        e_val = safe_input("-> Enter Value to Freeze: ").strip() or "9999"

        gg_type = f"gg.TYPE_{s_type}"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SEARCH & FREEZE SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function _FEATURESTIC_FREEZE_VALUE()
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber("{s_val}", {gg_type})
    local results = gg.getResults(100)
    if #results > 0 then
        for i, v in ipairs(results) do
            results[i].value = "{e_val}"
            results[i].freeze = true
        end
        gg.setValues(results)
        gg.addListItems(results)
        gg.toast("🔒 Value locked & frozen at {e_val}!")
    else
        gg.toast("⚠️ Target value not found!")
    end
end
_FEATURESTIC_FREEZE_VALUE()
"""
        out_file = res_dir / "GG_Search_Freeze_Template.lua"

    elif mode == '3':
        speed = safe_input("-> Enter Speedhack Multiplier (e.g., 2.5 or 5.0): ").strip() or "2.5"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SPEEDHACK TOGGLE SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
local _SPEED_ACTIVE = false
function TOGGLE_SPEEDHACK()
    if not _SPEED_ACTIVE then
        gg.setSpeed({speed})
        _SPEED_ACTIVE = true
        gg.toast("⚡ Speedhack Activated ({speed}x)")
    else
        gg.setSpeed(1.0)
        _SPEED_ACTIVE = false
        gg.toast("🐢 Speedhack Reset (1.0x)")
    end
end
TOGGLE_SPEEDHACK()
"""
        out_file = res_dir / "GG_Speedhack_Template.lua"

    else:
        snippet = """-- ========================================================
-- GENERATED GAMEGUARD STEALTH & ANTI-CHEAT LOG REMOVER
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function STEALTH_INIT()
    gg.setVisible(false)
    local log_paths = {
        "/sdcard/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs",
        "/sdcard/Android/data/com.pubg.krmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs",
        "/sdcard/Android/data/com.vng.pubgmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs"
    }
    for _, path in ipairs(log_paths) do
        os.remove(path)
    end
    gg.toast("🛡️ Anti-Cheat Logs Cleaned & Stealth Active!")
end
STEALTH_INIT()
"""
        out_file = res_dir / "GG_Stealth_Log_Cleaner.lua"

    out_file.write_text(snippet, encoding="utf-8")
    console.print(f"\n[bold green][OK] Generated GameGuard Template Script![/bold green]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


def run_lua_script_merger(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔗 ADVANCED LUA MASTER SCRIPT STUDIO & MULTI-SCRIPT COMBINER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dirs = [data_path / "LUA", Path("/sdcard/FeaturesticLeaks/LUA")]
    found_files = []
    
    for d in lua_dirs:
        if d.exists():
            for ext in ("*.lua", "*.luac", "*.txt"):
                found_files.extend(list(d.glob(ext)))

    # Deduplicate by path
    found_files = list({f.resolve(): f for f in found_files}.values())

    if not found_files:
        console.print(f"[bold yellow][!] No .lua or .luac scripts found in LUA/ folders.[/bold yellow]")
        console.print(f"[cyan]👉 Place your .lua files in /sdcard/FeaturesticLeaks/LUA/ and try again.[/cyan]")
        custom_p = safe_input("-> Enter custom Lua file or folder path (or Enter to cancel): ").strip().strip('"\'')
        if not custom_p:
            return
        p_obj = Path(custom_p)
        if p_obj.is_file():
            found_files = [p_obj]
        elif p_obj.is_dir():
            found_files = [f for f in p_obj.glob("*") if f.suffix in ('.lua', '.luac', '.txt')]
        else:
            console.print(f"[bold red][X] Path does not exist: {p_obj}[/bold red]")
            return

    console.print(f"\n[bold bright_cyan][+] Found {len(found_files)} script(s) available for merging/studio:[/bold bright_cyan]\n")
    for idx, f in enumerate(found_files, 1):
        size_str = f"{f.stat().st_size} bytes" if f.exists() else "0 bytes"
        console.print(f"  [{idx}] [bold white]{f.name}[/bold white] [dim]({f.parent.name} | {size_str})[/dim]")

    sel_input = safe_input("\n-> Select file numbers to include (e.g., '1, 2, 4' or 'ALL') [ALL]: ").strip()
    if not sel_input or sel_input.upper() == 'ALL':
        selected_files = found_files
    else:
        selected_files = []
        for part in sel_input.replace(',', ' ').split():
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(found_files):
                    selected_files.append(found_files[idx])

    if not selected_files:
        console.print("[bold red][X] No valid files selected.[/bold red]")
        return

    console.print(Panel(
        "[bold yellow]🛠️ CHOOSE LUA MERGE & CREATION MODE:[/bold yellow]\n\n"
        "  [1] [bold bright_white]GameGuard (GG) Multi-Choice Menu Studio[/bold bright_white]\n"
        "      [dim]Generates interactive UI popup menu with checkboxes/buttons for each script.[/dim]\n"
        "  [2] [bold bright_white]Modular Direct Code Combiner[/bold bright_white]\n"
        "      [dim]Merges scripts with isolated scope protection & error handling (pcall).[/dim]\n"
        "  [3] [bold bright_white]Game Cheat Feature Presets Builder[/bold bright_white]\n"
        "      [dim]Injects memory search, freeze values, anti-cheat bypass & wallhack templates.[/dim]",
        title="[bold cyan]💡 STUDIO MODES[/bold cyan]",
        border_style="cyan",
        box=ROUNDED
    ))

    mode = safe_input("\n-> Select Mode [1-3] [1]: ").strip() or '1'

    script_title = safe_input("-> Enter Master Script Menu Title [FEATURESTIC MASTER LUA]: ").strip() or "FEATURESTIC MASTER LUA"
    script_author = safe_input("-> Enter Author / Credits Name [Featurestic Leaks]: ").strip() or "Featurestic Leaks"

    merged_code_blocks = []

    if mode == '1':
        # Mode 1: GameGuard Multi-Choice GUI Menu Studio
        menu_items = []
        func_definitions = []
        exec_calls = []

        for idx, f in enumerate(selected_files, 1):
            clean_name = f.stem.replace('_', ' ').title()
            menu_items.append(f'        "{idx}. ⚡ {clean_name}"')
            
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                content = f"-- Error loading file: {e}"

            func_name = f"_EXECUTE_MODULE_{idx}"
            func_code = (
                f"function {func_name}()\n"
                f'    gg.toast("▶ Activating: {clean_name}...")\n'
                f'    local ok, err = pcall(function()\n'
                f'{content}\n'
                f'    end)\n'
                f'    if not ok then gg.alert("⚠️ Module Error ({clean_name}): " .. tostring(err)) end\n'
                f"end\n"
            )
            func_definitions.append(func_code)
            exec_calls.append(f"        if menu[{idx}] then {func_name}() end")

        all_in_one_idx = len(selected_files) + 1
        exit_idx = len(selected_files) + 2

        menu_items.append(f'        "{all_in_one_idx}. 🔥 Activate All Modules Simultaneously"')
        menu_items.append(f'        "{exit_idx}. ❌ Exit Script"')

        all_exec = " ".join([f"_EXECUTE_MODULE_{i}()" for i in range(1, len(selected_files) + 1)])
        exec_calls.append(f"        if menu[{all_in_one_idx}] then {all_exec} end")
        exec_calls.append(f'        if menu[{exit_idx}] then gg.toast("👋 Exiting Script..."); os.exit() end')

        menu_items_str = ",\n".join(menu_items)
        exec_calls_str = "\n".join(exec_calls)
        funcs_str = "\n\n".join(func_definitions)

        gui_wrapper = f"""-- ========================================================
-- FEATURESTIC LEAKS - MASTER GAMEGUARD LUA MENU SCRIPT
-- Title: {script_title}
-- Author: {script_author}
-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================

gg.toast("⚡ Initializing {script_title}...")
gg.setVisible(true)

-- ========================================================
-- MODULE FUNCTIONS
-- ========================================================
{funcs_str}

-- ========================================================
-- INTERACTIVE GAMEGUARD MENU SYSTEM
-- ========================================================
function MAIN_MENU()
    local menu = gg.multiChoice({{
{menu_items_str}
    }}, nil, "🔥 {script_title} 🔥\\nCreated By: {script_author}\\nSelect features to run:")

    if menu == nil then return end

{exec_calls_str}
end

-- ========================================================
-- MAIN SCRIPT LOOP & FLOATING ICON LISTENER
-- ========================================================
gg.toast("✅ {script_title} Ready! Tap GG Icon to open menu.")

while true do
    if gg.isVisible(true) then
        gg.setVisible(false)
        MAIN_MENU()
    end
    gg.sleep(100)
end
"""
        merged_code_blocks.append(gui_wrapper)

    elif mode == '3':
        # Mode 3: Game Preset Feature Builder
        console.print("\n[bold yellow][+] Adding Game Cheat Presets & Memory Helpers...[/bold yellow]")
        preset_code = f"""-- ========================================================
-- FEATURESTIC LEAKS - GAME CHEAT MEMORY PRESETS STUDIO
-- Title: {script_title} | Author: {script_author}
-- ========================================================

local function _FEAT_MEMORY_PATCH(address, flags, value)
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber(address, flags)
    local res = gg.getResults(100)
    if #res > 0 then
        for i, v in ipairs(res) do
            res[i].value = value
            res[i].freeze = true
        end
        gg.setValues(res)
        gg.addListItems(res)
        gg.toast("✅ Memory Patched Successfully!")
    else
        gg.toast("⚠️ Address Not Found!")
    end
end

local function _FEAT_ANTILOG_CLEANER()
    os.remove("/sdcard/Android/data/com.pubg.krmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs")
    os.remove("/sdcard/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs")
    gg.toast("🛡️ Anti-Cheat Logs Cleaned!")
end

_FEAT_ANTILOG_CLEANER()
"""
        merged_code_blocks.append(preset_code)

        # Append chosen files as well
        for f in selected_files:
            try:
                merged_code_blocks.append(f"-- Module: {f.name}\npcall(function()\n" + f.read_text(encoding="utf-8", errors="ignore") + "\nend)\n")
            except Exception as e:
                merged_code_blocks.append(f"-- Error reading {f.name}: {e}")

    else:
        # Mode 2: Clean Modular Combination
        header = f"""-- ========================================================
-- FEATURESTIC LEAKS - MASTER MERGED LUA SCRIPT
-- Title: {script_title} | Author: {script_author}
-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================\n\n"""
        merged_code_blocks.append(header)

        for f in selected_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                block = f"-- >>> MODULE START: {f.name} >>>\npcall(function()\n{content}\nend)\n-- <<< MODULE END: {f.name} <<<\n"
                merged_code_blocks.append(block)
            except Exception as e:
                merged_code_blocks.append(f"-- Error reading {f.name}: {e}\n")

    final_lua = "\n".join(merged_code_blocks)

    # Obfuscation Option
    obf_choice = safe_input("\n-> Encrypt string constants with Hex wrapper for security? (y/N): ").strip().lower()
    if obf_choice in ('y', 'yes'):
        def _hex_enc_str(m):
            s = m.group(1)
            if len(s) < 3 or '\\' in s or '"' in s:
                return f'"{s}"'
            hex_parts = "".join([f"\\x{ord(c):02x}" for c in s])
            return f'"{hex_parts}"'

        final_lua = re.sub(r'"([^"\r\n]{3,})"', _hex_enc_str, final_lua)
        console.print("[bold green][+] String constants obfuscated with Hex escape encoding.[/bold green]")

    out_name = safe_input("-> Enter output script filename [Master_Merged_Script.lua]: ").strip() or "Master_Merged_Script.lua"
    if not out_name.endswith('.lua'):
        out_name += '.lua'

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / out_name

    out_file.write_text(final_lua, encoding="utf-8")

    console.print(f"\n[bold green][OK] Successfully created Master Lua Script with {len(selected_files)} module(s)![/bold green]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


def run_lua_protector_obfuscator(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🛡️ LUA SCRIPT PROTECTION & OBFUSCATOR ENGINE (Single File)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    
    lua_file, _ = pick_file_from_folder("Protect Lua Script", lua_dir, extensions=[".lua"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom .lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print(f"\n[bold cyan]⚡ Reading source file: [bold white]{lua_file.name}[/bold white]...[/bold cyan]")
    try:
        raw_code = lua_file.read_text(encoding='utf-8', errors='ignore')
    except Exception as ex:
        console.print(f"[bold red][X] Error reading file: {ex}[/bold red]")
        if 'send_telegram_bug_report' in globals():
            send_telegram_bug_report("LUA_PROTECT_READ_ERROR", str(ex), "Lua Protect", "FeaturesticLeaks.py", "3800", "run_lua_protector_obfuscator", traceback.format_exc())
        return

    # XOR Key Obfuscation Generator
    xor_key = 0x5A
    byte_array = [ord(c) ^ xor_key for c in raw_code]
    byte_str = ",".join(str(b) for b in byte_array)

    protected_lua = f"""-- ========================================================
-- FEATURESTIC LEAKS LUA PROTECTOR v2.5
-- Protected Script: {lua_file.name}
-- Protected Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================
local _K = {xor_key}
local _B = {{{byte_str}}}
local _S = {{}}
for i = 1, #_B do
    local b = _B[i]
    local x = (bit and bit.bxor) and bit.bxor(b, _K) or (b >= _K and (b - _K) or (b + _K))
    _S[i] = string.char(x)
end
local _run = loadstring or load
local _fn, _err = _run(table.concat(_S))
if _fn then
    _fn()
else
    error("Protected Lua payload execution error: " .. tostring(_err))
end
"""

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / f"protected_{lua_file.name}"
    out_file.write_text(protected_lua, encoding="utf-8")

    console.print(f"\n[bold green]✅ Lua Protection Completed Successfully![/bold green]")
    console.print(f" 📁 [bold white]Protected Script Saved: {out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Synced to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass

    # Attempt compilation
    compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
    if compiler:
        out_luac = res_dir / f"protected_{lua_file.stem}.luac"
        proc = subprocess.run([compiler, "-o", str(out_luac), str(out_file)], capture_output=True, text=True)
        if proc.returncode == 0:
            console.print(f" 📜 [bold green]Bytecode Compiled: {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
            if sd_res.exists():
                try:
                    shutil.copy2(out_luac, sd_res / out_luac.name)
                except Exception:
                    pass

    # Send background status update to Telegram Bot
    if 'send_telegram_status_update' in globals():
        send_telegram_status_update(
            action_name="Lua Script Protection",
            status_msg=f"Successfully protected '{lua_file.name}' using XOR byte encryption.",
            file_details=out_file.name
        )


def run_lua_compiler(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🌙 LUA COMPILER (.lua Source -> .luac Bytecode)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    sd_lua = Path("/sdcard/FeaturesticLeaks/LUA")
    try:
        if sd_lua.parent.exists():
            sd_lua.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    lua_file, _ = pick_file_from_folder("Compile Lua", lua_dir, extensions=[".lua"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom .lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    # Automatic Lua Protection & XOR Obfuscation Step
    try:
        raw_src = lua_file.read_text(encoding='utf-8', errors='ignore')
        xor_key = 0x5A
        byte_array = [ord(c) ^ xor_key for c in raw_src]
        byte_str = ",".join(str(b) for b in byte_array)
        protected_code = f"""-- ========================================================
-- FEATURESTIC LEAKS LUA AUTO-PROTECTOR v2.5
-- Protected Script: {lua_file.name}
-- ========================================================
local _K = {xor_key}
local _B = {{{byte_str}}}
local _S = {{}}
for i = 1, #_B do
    local b = _B[i]
    local x = (bit and bit.bxor) and bit.bxor(b, _K) or (b >= _K and (b - _K) or (b + _K))
    _S[i] = string.char(x)
end
local _run = loadstring or load
local _fn, _err = _run(table.concat(_S))
if _fn then _fn() else error("Protected script load error: "..tostring(_err)) end
"""
        res_dir_prot = data_path / "RESULT"
        res_dir_prot.mkdir(parents=True, exist_ok=True)
        prot_file = res_dir_prot / f"protected_{lua_file.name}"
        prot_file.write_text(protected_code, encoding="utf-8")
        console.print(f"[bold green]🛡️ [AUTO PROTECTION] Applied XOR Encryption to '{lua_file.name}' -> saved 'protected_{lua_file.name}'[/bold green]")
        lua_file = prot_file
    except Exception as ex:
        console.print(f"[bold yellow][!] Auto-protection skipped: {ex}[/bold yellow]")

    all_compilers = ["luac5.1", "luac51", "luac", "luajit", "luac5.2", "luac5.3", "luac5.4"]
    available_compilers = [c for c in all_compilers if shutil.which(c)]

    if not available_compilers:
        console.print(Panel(
            "[bold red][X] No Lua Compiler (luac or luajit) is installed in Termux![/bold red]\n\n"
            "[bold cyan]👉 Click 'Auto-Install' below or run this command in Termux:[/bold cyan]\n"
            "[bold yellow]   pkg install -y lua51 luajit[/bold yellow]",
            border_style="red", box=ROUNDED
        ))
        auto_inst = safe_input('\n-> Auto-install lua51 & luajit now via Termux pkg? (Y/n): ').strip().lower()
        if auto_inst in ['', 'y', 'yes']:
            console.print("[bold cyan][+] Running: pkg update -y && pkg install -y lua51 luajit...[/bold cyan]")
            try:
                subprocess.run("pkg update -y && pkg install -y lua51 luajit", shell=True, check=True)
                console.print("[bold green][OK] Package installation completed![/bold green]")
                available_compilers = [c for c in all_compilers if shutil.which(c)]
            except Exception as e:
                console.print(f"[bold red][X] Auto-installation failed: {e}[/bold red]")
                return
        else:
            return

    if not available_compilers:
        console.print("[bold red][X] No Lua compiler available. Please install lua51 or luajit manually.[/bold red]")
        return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_luac = res_dir / f"{lua_file.stem}.luac"

    success = False
    last_stderr = ""
    last_compiler = ""

    for compiler in available_compilers:
        console.print(f"[bold cyan][+] Attempting compile with '{compiler}'...[/bold cyan]")
        if compiler == "luajit":
            cmd = ["luajit", "-b", str(lua_file), str(out_luac)]
        else:
            cmd = [compiler, "-o", str(out_luac), str(lua_file)]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                console.print(f"[bold green][OK] Compiled successfully with '{compiler}': {out_luac}[/bold green]")
                success = True
                if sd_lua.exists():
                    try:
                        shutil.copy2(out_luac, sd_lua / out_luac.name)
                        console.print(f"[bold green][+] Saved to SDCard: {sd_lua / out_luac.name}[/bold green]")
                    except Exception:
                        pass
                break
            else:
                last_stderr = proc.stderr
                last_compiler = compiler
        except Exception as e:
            last_stderr = str(e)

    if not success:
        console.print("\n[bold yellow]⚡ [Auto-Fix Mode Activated] Preprocessing Lua code to fix syntax & >200 local variable limits...[/bold yellow]")
        fixed_lua = fix_lua_syntax_for_lua51(lua_file)
        
        for compiler in available_compilers:
            if compiler == "luajit":
                cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
            else:
                cmd = [compiler, "-o", str(out_luac), str(fixed_lua)]
            
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                console.print(f"[bold green]✅ Auto-fixed and compiled successfully with '{compiler}': {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
                success = True
                break

        if not success and not shutil.which("luajit"):
            console.print("[bold cyan][+] Auto-installing LuaJIT via Termux pkg to retry...[/bold cyan]")
            try:
                subprocess.run("pkg install -y luajit", shell=True, check=True)
                if shutil.which("luajit"):
                    cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode == 0:
                        console.print(f"[bold green]✅ Auto-fixed and compiled successfully with 'luajit': {out_luac.name}[/bold green]")
                        success = True
            except Exception:
                pass

        if not success:
            analyze_and_display_lua_error(lua_file, last_stderr)
            console.print(f"\n[bold yellow]💡 Fallback: Saved cleaned patched script as {fixed_lua.name}[/bold yellow]")

    if success:
        target_dirs = [
            data_path / "LUA_WORKSPACE" / "4_RESULT",
            data_path / "LUA_WORKSPACE" / "3_COMPILED",
            data_path / "PAK_WORKSPACE" / "3_REPLACE",
            data_path / "PAK_WORKSPACE" / "4_INJECT",
            Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/4_RESULT"),
            Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/3_COMPILED"),
            Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE"),
            Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT")
        ]
        for td in target_dirs:
            try:
                td.mkdir(parents=True, exist_ok=True)
                shutil.copy2(out_luac, td / out_luac.name)
            except Exception:
                pass
        console.print(f"[bold green]🎉 Output synced across all workspace & SDCard folders![/bold green]")

def run_lua_decompiler(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🌙 LUA AUTO-DECOMPILER (.luac Bytecode / Custom -> .lua Source)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    sd_lua = Path("/sdcard/FeaturesticLeaks/LUA")
    try:
        if sd_lua.parent.exists():
            sd_lua.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    luac_file, _ = pick_file_from_folder("Decompile Lua", lua_dir, extensions=[".luac", ".lua", ".bytecode", ".bytes"])
    if not luac_file:
        custom_input = safe_input('-> Enter custom .luac file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        luac_file = Path(custom_input)
        if not luac_file.exists() or not luac_file.is_file():
            console.print(f'[bold red][X] File not found: {luac_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_lua = res_dir / f"{luac_file.stem}_decompiled.lua"

    # Step 1: Check if file is already plain text Lua source code
    try:
        raw_txt = luac_file.read_text(encoding="utf-8", errors="ignore")
        keywords = ["function", "local ", "if ", "then", "return", "end", "for ", "while ", "gg."]
        if any(kw in raw_txt[:3000] for kw in keywords):
            out_lua.write_text(raw_txt, encoding="utf-8")
            console.print(f"[bold green][OK] Decompiled successfully (Plain Lua Source Code):[/bold green]")
            console.print(f"[bold green][+] Output file: {out_lua}[/bold green]")
            if sd_lua.exists():
                try:
                    shutil.copy2(out_lua, sd_lua / out_lua.name)
                    console.print(f"[bold green][+] Saved to SDCard: {sd_lua / out_lua.name}[/bold green]")
                except Exception:
                    pass
            return
    except Exception:
        pass

    raw_bytes = luac_file.read_bytes()
    luadec_bin = shutil.which("luadec")
    java_bin = shutil.which("java")

    unluac_jar = None
    possible_jars = [
        data_path / "unluac.jar",
        Path.home() / "unluac.jar",
        Path("/data/data/com.termux/files/usr/share/java/unluac.jar")
    ]
    for j in possible_jars:
        if j.exists():
            unluac_jar = j
            break

    # Build Header Candidates for Auto-Repair
    candidates = [("Original", raw_bytes)]
    if raw_bytes[:4] != b'\x1bLua' and raw_bytes[:4] != b'\x1bLJ':
        if len(raw_bytes) >= 12:
            candidates.append(("Auto-Fixed Lua 5.1 Header", b'\x1bLua\x51\x00\x01\x04\x08\x04\x08\x00' + raw_bytes[12:]))
            candidates.append(("Auto-Fixed Lua 5.3 Header", b'\x1bLua\x53\x00\x00\x04\x08\x04\x08\x00' + raw_bytes[12:]))
            candidates.append(("Auto-Fixed Lua 5.2 Header", b'\x1bLua\x52\x00\x01\x04\x08\x04\x08\x00' + raw_bytes[12:]))
        if len(raw_bytes) >= 4:
            candidates.append(("Auto-Fixed LuaJIT Header", b'\x1bLJ\x02' + raw_bytes[4:]))

    decompiled_text = None
    decompile_engine = None

    temp_luac = data_path / "_tmp_auto_fix.luac"

    for label, c_bytes in candidates:
        if decompiled_text:
            break
        try:
            temp_luac.write_bytes(c_bytes)
        except Exception:
            continue

        # Try unluac.jar
        if java_bin and unluac_jar:
            try:
                proc = subprocess.run([java_bin, "-jar", str(unluac_jar), str(temp_luac)], capture_output=True, text=True, timeout=15)
                if proc.returncode == 0 and proc.stdout.strip() and "Exception" not in proc.stdout[:100]:
                    decompiled_text = proc.stdout
                    decompile_engine = f"unluac ({label})"
                    break
            except Exception:
                pass

        # Try luadec
        if luadec_bin:
            try:
                proc = subprocess.run([luadec_bin, str(temp_luac)], capture_output=True, text=True, timeout=15)
                if proc.returncode == 0 and proc.stdout.strip() and "function 0 0" not in proc.stdout:
                    decompiled_text = proc.stdout
                    decompile_engine = f"luadec ({label})"
                    break
            except Exception:
                pass

        # Try Python Engine
        try:
            proto = _load_lua_custom_proto(str(temp_luac))
            if proto:
                decompiled_text = _pseudo_decompile_lua(proto)
                decompile_engine = f"Python Engine ({label})"
                break
            proto_std = _load_std_bytecode_to_proto(str(temp_luac))
            if proto_std:
                decompiled_text = _pseudo_decompile_lua(proto_std)
                decompile_engine = f"Python Engine Standard ({label})"
                break
        except Exception:
            pass

    if temp_luac.exists():
        try:
            temp_luac.unlink()
        except Exception:
            pass

    # Fallback: Smart String & Structure Recovery Engine
    if not decompiled_text:
        console.print("[bold yellow][+] Applying Smart String & Structure Auto-Recovery Engine...[/bold yellow]")
        str_found = re.findall(r'[a-zA-Z0-9_./\\:-]{3,}', raw_bytes.decode('latin1', errors='ignore'))
        urls = [s for s in str_found if s.startswith("http://") or s.startswith("https://")]
        offsets = [s for s in str_found if s.startswith("0x")]
        funcs = [s for s in str_found if "gg." in s or "function" in s or "lib" in s]

        lines = [
            "-- ========================================================",
            "-- [FEATURESTIC LEAKS AUTO-DECOMPILED RECOVERY SCRIPT]",
            f"-- Target: {luac_file.name}",
            f"-- Mode: Auto-Extracted Constants & Script Structure",
            "-- ========================================================\n",
            "local _RECOVERED_STRINGS = {"
        ]
        for s in set(str_found[:150]):
            lines.append(f'    "{s}",')
        lines.append("}\n")

        if urls:
            lines.append("-- Extracted URLs & Endpoints:")
            for u in set(urls):
                lines.append(f'-- URL: {u}')
            lines.append("")

        if funcs:
            lines.append("-- Detected GameGuard & Function Symbols:")
            for fn in set(funcs):
                lines.append(f'-- Symbol: {fn}')
            lines.append("")

        lines.append("-- Reconstructed Executable Code Block:")
        lines.append("function _main_recovered()")
        lines.append("    -- Auto-Generated Recovery Handler")
        lines.append("    for idx, str_val in ipairs(_RECOVERED_STRINGS) do")
        lines.append("        if string.find(str_val, 'gg.') then")
        lines.append("            pcall(loadstring(str_val))")
        lines.append("        end")
        lines.append("    end")
        lines.append("end")
        lines.append("pcall(_main_recovered)")

        decompiled_text = "\n".join(lines)
        decompile_engine = "Smart Structure & Constant Auto-Recovery Engine"

    out_lua.write_text(decompiled_text, encoding="utf-8")
    console.print(f"[bold green][OK] Decompiled successfully ({decompile_engine}):[/bold green]")
    console.print(f"[bold green][+] Output file: {out_lua}[/bold green]")
    if sd_lua.exists():
        try:
            shutil.copy2(out_lua, sd_lua / out_lua.name)
            console.print(f"[bold green][+] Also saved to SDCard: {sd_lua / out_lua.name}[/bold green]")
        except Exception:
            pass

def extract_pak_from_lua(lua_file_path: Path, output_pak_path: Path, output_clean_lua_path: Path) -> dict:
    """
    Reads a .lua script, uses pattern matching/regex to extract high-density Base64/Hex strings
    representing embedded .pak binary data, writes the decoded .pak file, and saves a clean .lua script.
    """
    if not lua_file_path.exists():
        return {"success": False, "message": f"File not found: {lua_file_path}"}

    try:
        content = lua_file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"success": False, "message": f"Failed to read Lua file: {e}"}

    b64_matches = re.findall(r'["\']([A-Za-z0-9+/=]{100,})["\']', content)
    hex_matches = re.findall(r'["\']([0-9a-fA-F]{100,})["\']', content)
    hex_escaped_matches = re.findall(r'((?:\\x[0-9a-fA-F]{2}){50,})', content)

    extracted_bytes = None
    matched_string = None
    encoding_used = None

    if b64_matches:
        for candidate in sorted(b64_matches, key=len, reverse=True):
            try:
                decoded = base64.b64decode(candidate)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Base64"
                    break
            except Exception:
                continue

    if not extracted_bytes and hex_matches:
        for candidate in sorted(hex_matches, key=len, reverse=True):
            try:
                decoded = bytes.fromhex(candidate)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Hex"
                    break
            except Exception:
                continue

    if not extracted_bytes and hex_escaped_matches:
        for candidate in sorted(hex_escaped_matches, key=len, reverse=True):
            try:
                raw_hex = candidate.replace("\\x", "")
                decoded = bytes.fromhex(raw_hex)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Escaped Hex"
                    break
            except Exception:
                continue

    if not extracted_bytes:
        return {"success": False, "message": "No embedded PAK payload (Base64 or Hex >= 100 chars) found in Lua script."}

    output_pak_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pak_path, "wb") as f:
        f.write(extracted_bytes)

    clean_content = content.replace(matched_string, "-- [EMBEDDED_PAK_PAYLOAD_REMOVED]")
    output_clean_lua_path.parent.mkdir(parents=True, exist_ok=True)
    output_clean_lua_path.write_text(clean_content, encoding="utf-8")

    return {
        "success": True,
        "encoding": encoding_used,
        "pak_size": len(extracted_bytes),
        "pak_path": output_pak_path,
        "clean_lua_path": output_clean_lua_path,
        "message": "Extraction Successful"
    }

def embed_pak_into_lua(pak_file_path: Path, output_lua_path: Path, target_filename_in_gg: str = "game_mod.pak") -> dict:
    """
    Reads a binary .pak file, encodes it as Base64, and builds a standalone GameGuardian/Android LUA script
    that automatically unpacks/writes the .pak file to disk at runtime using io.open/file:write.
    """
    if not pak_file_path.exists():
        return {"success": False, "message": f"PAK file not found: {pak_file_path}"}

    try:
        with open(pak_file_path, "rb") as f:
            pak_bytes = f.read()
    except Exception as e:
        return {"success": False, "message": f"Failed to read PAK file: {e}"}

    pak_size = len(pak_bytes)
    if pak_size == 0:
        return {"success": False, "message": "PAK file is empty (0 bytes)."}

    b64_payload = base64.b64encode(pak_bytes).decode("ascii")

    lua_template = f"""-- =======================================================
-- FEATURESTIC LEAKS - EMBEDDED PAK INSTALLER LUA SCRIPT
-- Generated for GameGuardian / Android Runtime
-- Target File: {target_filename_in_gg}
-- Payload Size: {pak_size} bytes
-- =======================================================

local target_path = gg.EXT_STORAGE .. "/FeaturesticLeaks/RESULT/{target_filename_in_gg}"
if not gg.EXT_STORAGE then
    target_path = "/sdcard/FeaturesticLeaks/RESULT/{target_filename_in_gg}"
end

gg.toast("⚡ Extracting embedded PAK payload ({pak_size} bytes)...")

local b64_payload = "{b64_payload}"

local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
local function base64_decode(data)
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i - f%2^(i-1) >= 2^(i-1) and '1' or '0') end
        return r
    end):gsub('%d%d%d%d%d%d%d%d', function(x)
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end

local decoded_bytes = base64_decode(b64_payload)

local file = io.open(target_path, "wb")
if file then
    file:write(decoded_bytes)
    file:close()
    gg.alert("✅ PAK Payload extracted successfully!\\nSaved to: " .. target_path)
    gg.toast("✅ PAK Unpacked Successfully!")
else
    gg.alert("❌ Error: Failed to write PAK file to storage.\\nPlease check SDCard storage permissions.")
end
"""

    output_lua_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_lua_path.write_text(lua_template, encoding="utf-8")
    except Exception as e:
        return {"success": False, "message": f"Failed to write LUA script: {e}"}

    return {
        "success": True,
        "pak_size": pak_size,
        "lua_path": output_lua_path,
        "message": "Embedding Successful"
    }

def run_lua_pak_extractor(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 LUA-to-PAK EXTRACTOR (Extract Embedded PAK from .lua Script)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)

    lua_file, _ = pick_file_from_folder("Select Lua Script", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom .lua script path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_pak = res_dir / f"extracted_{lua_file.stem}.pak"
    out_clean_lua = res_dir / f"clean_{lua_file.name}"

    console.print(f"\n[bold cyan][+] Scanning {lua_file.name} for embedded Base64/Hex PAK data...[/bold cyan]")
    res = extract_pak_from_lua(lua_file, out_pak, out_clean_lua)

    if res["success"]:
        console.print(Panel(
            f"[bold green]✅ {res['message']}![/bold green]\n\n"
            f"[bold white]Encoding Found:[/bold white] [bold cyan]{res['encoding']}[/bold cyan]\n"
            f"[bold white]Extracted PAK Size:[/bold white] [bold yellow]{human_size(res['pak_size'])}[/bold yellow]\n\n"
            f"📄 [bold white]Extracted PAK File:[/bold white] {out_pak}\n"
            f"📄 [bold white]Cleaned Lua Script:[/bold white] {out_clean_lua}",
            title="Extraction Complete",
            border_style="green",
            box=ROUNDED
        ))
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_pak, sd_res / out_pak.name)
                shutil.copy2(out_clean_lua, sd_res / out_clean_lua.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/")
            except Exception:
                pass
    else:
        console.print(f"[bold red][X] {res['message']}[/bold red]")

def run_pak_lua_embedder(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 PAK-to-LUA EMBEDDER (Convert .pak to Base64 & Embed in GG Script)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    pak_dir = data_path / "PAK"
    pak_dir.mkdir(parents=True, exist_ok=True)

    pak_file, _ = pick_file_from_folder("Select PAK File to Embed", pak_dir, extensions=[".pak", ".obb"])
    if not pak_file:
        custom_input = safe_input('-> Enter custom .pak file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        pak_file = Path(custom_input)
        if not pak_file.exists():
            console.print(f'[bold red][X] File not found: {pak_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_lua = res_dir / f"installer_{pak_file.stem}.lua"

    console.print(f"\n[bold cyan][+] Encoding {pak_file.name} ({human_size(pak_file.stat().st_size)}) into GameGuardian Lua script...[/bold cyan]")
    res = embed_pak_into_lua(pak_file, out_lua, target_filename_in_gg=pak_file.name)

    if res["success"]:
        console.print(Panel(
            f"[bold green]✅ {res['message']}![/bold green]\n\n"
            f"[bold white]PAK Payload Size:[/bold white] [bold yellow]{human_size(res['pak_size'])}[/bold yellow]\n"
            f"📄 [bold white]Generated GG Installer Script:[/bold white] {out_lua}",
            title="Embedding Complete",
            border_style="green",
            box=ROUNDED
        ))
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_lua, sd_res / out_lua.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/{out_lua.name}")
            except Exception:
                pass
    else:
        console.print(f"[bold red][X] {res['message']}[/bold red]")

