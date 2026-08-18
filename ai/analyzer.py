import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
from rich.markup import escape

from ai.assistant import call_ai_api
from core.ui import safe_input

console = Console()

def extract_lua_functions_and_symbols(file_path: Path) -> Dict[str, Any]:
    """
    Extracts functions, methods, hooks, tables, and interesting string constants from a Lua file.
    """
    results = {
        "file": file_path.name,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "functions": [],
        "tables": [],
        "hooks": [],
        "strings": []
    }
    
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        
        func_patterns = [
            re.compile(r'^\s*function\s+([a-zA-Z0-9_\.\:]+)\s*\((.*?)\)'),
            re.compile(r'^\s*local\s+function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)'),
            re.compile(r'^\s*([a-zA-Z0-9_\.\:]+)\s*=\s*function\s*\((.*?)\)')
        ]
        
        table_pattern = re.compile(r'^\s*([a-zA-Z0-9_]+)\s*=\s*\{')
        hook_pattern = re.compile(r'([a-zA-Z0-9_\.\:]*(?:Hook|Register|Callback|Event|Listener|On[A-Z][a-zA-Z0-9_]+)[a-zA-Z0-9_\.\:]*)')
        string_pattern = re.compile(r'["\']([a-zA-Z0-9_\/\.\-]{4,60})["\']')
        
        seen_funcs = set()
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
                
            for pat in func_patterns:
                m = pat.search(line)
                if m:
                    fname = m.group(1).strip()
                    params = m.group(2).strip()
                    if fname not in seen_funcs:
                        seen_funcs.add(fname)
                        results["functions"].append({
                            "name": fname,
                            "params": params,
                            "line": idx
                        })
                    break
                    
            tm = table_pattern.search(line)
            if tm:
                tname = tm.group(1).strip()
                if tname not in results["tables"] and len(results["tables"]) < 25:
                    results["tables"].append(tname)
                    
            hm = hook_pattern.search(line)
            if hm:
                hname = hm.group(1).strip()
                if hname not in results["hooks"] and len(results["hooks"]) < 25:
                    results["hooks"].append(hname)
                    
            sm = string_pattern.findall(line)
            for s in sm:
                if any(kw in s.lower() for kw in ['lua', 'actor', 'player', 'weapon', 'recoil', 'speed', 'bullet', 'camera', 'damage', 'config', 'game', 'sound']):
                    if s not in results["strings"] and len(results["strings"]) < 30:
                        results["strings"].append(s)
                        
    except Exception as e:
        results["error"] = str(e)
        
    return results

def scan_unpacked_directory(dir_path: Path) -> List[Dict[str, Any]]:
    """
    Recursively scans an unpacked folder for Lua and asset files and extracts symbol metadata.
    """
    scanned_data = []
    if not dir_path.exists():
        return scanned_data
        
    lua_files = [p for p in dir_path.rglob("*") if p.is_file() and p.suffix.lower() in ['.lua', '.luac', '.txt']]
    for lf in lua_files[:50]: # limit to top 50 scripts for responsiveness
        info = extract_lua_functions_and_symbols(lf)
        if info.get("functions") or info.get("tables"):
            scanned_data.append(info)
            
    return scanned_data

def run_ai_function_mod_generator(data_path: Path):
    """
    Interactive workflow: Scans unpacked files -> displays functions -> prompts user -> generates tailored Lua mod script.
    """
    console.print(Panel(
        "[bold bright_cyan]🧠 AI UNPACKED CODE SCANNER & LUA GENERATOR 🧠[/bold bright_cyan]\n\n"
        "[bold white]Yeh tool unpacked PAK/Lua files ko scan karke unke Functions, Hooks aur Logic analyze karta hai,[/bold white]\n"
        "[bold bright_yellow]aur aapki demand ke hisaab se exact compatible Lua 5.1 mod script generate karta hai![/bold bright_yellow]",
        border_style="bright_cyan",
        box=ROUNDED
    ))

    # 1. Locate unpacked directory or PAK
    candidates = [
        data_path / "UNPACK",
        data_path / "RESULT",
        data_path / "LUA",
        Path("/sdcard/FeaturesticLeaks/UNPACK"),
        Path("/sdcard/FeaturesticLeaks/RESULT"),
        Path("/sdcard/FeaturesticLeaks/LUA")
    ]
    
    found_dirs = []
    for c in candidates:
        if c.exists():
            for sub in c.iterdir():
                if sub.is_dir() and not sub.name.startswith("."):
                    found_dirs.append(sub)
            if c.name in ['LUA'] and any(c.glob("*.lua")):
                found_dirs.append(c)

    # If no unpacked folder found, look for PAKs to unpack
    if not found_dirs:
        pak_dirs = [data_path / "PAK", data_path / "INPUT", Path("/sdcard/FeaturesticLeaks/PAK"), Path("/sdcard/FeaturesticLeaks/INPUT")]
        paks = [f for pd in pak_dirs if pd.exists() for f in pd.glob("*") if f.is_file() and f.suffix.lower() in ['.pak', '.obb']]
        if paks:
            console.print(f"[bold yellow]💡 Unpacked folder nahi mila, par [white]{len(paks)} PAK[/white] file(s) mili hain.[/bold yellow]")
            auto_un = safe_input("Kya pehle PAK unpack karun taaki functions scan kar sakein? (y/n) [y]: ").strip().lower()
            if auto_un in ['', 'y', 'yes', 'haan', '1']:
                try:
                    from pak.container import TencentPakFile
                    target_pak = paks[0]
                    console.print(f"[bold cyan]⚡ Unpacking [white]{target_pak.name}[/white]...[/bold cyan]")
                    pak_obj = TencentPakFile(target_pak)
                    out_un = data_path / "UNPACK" / target_pak.stem
                    pak_obj.dump(out_un)
                    console.print(f"[bold green]✅ PAK unpacked to: {out_un}[/bold green]")
                    found_dirs.append(out_un)
                except Exception as ex:
                    console.print(f"[bold red]❌ Unpack failed: {ex}[/bold red]")

    if not found_dirs:
        console.print("[bold red]❌ Koi unpacked folder ya Lua scripts nahi mile![/bold red]")
        console.print("[dim]Pehle PAK unpack karein ya LUA folder me scripts copy karein.[/dim]\n")
        return

    # Let user select target directory
    console.print("\n[bold bright_cyan]📂 Target Unpacked Folders / Scripts Found:[/bold bright_cyan]")
    for i, d in enumerate(found_dirs, 1):
        console.print(f" [bold bright_yellow][{i}][/bold bright_yellow] [bold white]{d.name}[/bold white] [dim]({d})[/dim]")
        
    choice = safe_input(f"\nSelect folder to scan [1-{len(found_dirs)}] [1]: ").strip()
    idx = 0
    if choice.isdigit() and 1 <= int(choice) <= len(found_dirs):
        idx = int(choice) - 1
        
    selected_dir = found_dirs[idx]
    console.print(f"\n[bold cyan]🔍 Scanning functions & symbols in: [white]{selected_dir.name}[/white]...[/bold cyan]")
    scanned_results = scan_unpacked_directory(selected_dir)
    
    if not scanned_results:
        console.print("[bold yellow]⚠️ Is folder me direct text-based Lua functions nahi mile.[/bold yellow]")
        console.print("[dim]Aap manual prompt se bhi custom Lua script generate kar sakte hain![/dim]")
    else:
        # Render discovered functions table
        table = Table(
            title=f"[bold bright_green]⚡ DISCOVERED FUNCTIONS & SYMBOLS IN {selected_dir.name} ⚡[/bold bright_green]",
            box=ROUNDED,
            border_style="bright_green",
            expand=True
        )
        table.add_column("FILE", style="bold yellow", width=20)
        table.add_column("FUNCTIONS / METHODS", style="bold bright_white")
        table.add_column("HOOKS / TABLES", style="bright_cyan")
        
        all_funcs_summary = []
        for item in scanned_results[:12]:
            funcs_list = [f"• {escape(f['name'])}({escape(f['params'])})" for f in item['functions'][:5]]
            funcs_str = "\n".join(funcs_list)
            if len(item['functions']) > 5:
                funcs_str += f"\n[dim]+{len(item['functions']) - 5} more functions...[/dim]"
                
            hooks_escaped = [escape(h) for h in (item['hooks'][:3] + item['tables'][:3])]
            hooks_str = ", ".join(hooks_escaped)
            table.add_row(escape(item['file']), funcs_str if funcs_str else "[dim]No direct funcs[/dim]", hooks_str if hooks_str else "[dim]-[/dim]")
            
            for f in item['functions']:
                all_funcs_summary.append(f"{item['file']} -> {f['name']}({f['params']})")
                
        console.print(table)

    # Ask user for modification demand
    console.print(Panel(
        "[bold bright_yellow]💡 AI SCRIPT GENERATOR PROMPT[/bold bright_yellow]\n\n"
        "[bold white]Batao bhai isme kya feature ya modification chahiye?[/bold white]\n"
        "[dim]Examples:\n"
        " • 'Recoil control function hook bana ke do'\n"
        " • 'Player speed and bullet parameters modify karne ka safe script banao'\n"
        " • 'GameGuard memory search & edit function bana do'[/dim]",
        border_style="yellow",
        box=ROUNDED
    ))
    
    user_goal = safe_input("\n💬 Enter Feature Demand / Modification Request: ").strip()
    if not user_goal:
        console.print("[bold dim]Operation cancelled.[/bold dim]")
        return
        
    console.print("\n[bold bright_cyan]🤖 OpenCode AI Engine is analyzing functions & generating Lua 5.1 script...[/bold bright_cyan]")
    
    # Prepare rich context prompt
    context_snippet = ""
    if scanned_results:
        context_snippet = "ACTUAL FUNCTIONS & SYMBOLS DISCOVERED IN TARGET GAME UNPACK:\n"
        for item in scanned_results[:8]:
            context_snippet += f"File: {item['file']}\n"
            for fn in item['functions'][:6]:
                context_snippet += f"  - function {fn['name']}({fn['params']})\n"
            if item.get('hooks'):
                context_snippet += f"  - Hooks/Events: {', '.join(item['hooks'][:4])}\n"
            if item.get('tables'):
                context_snippet += f"  - Tables: {', '.join(item['tables'][:4])}\n"
            context_snippet += "\n"

    ai_prompt = (
        "You are Featurestic Leaks AI Code Generator specialized in Lua 5.1 scripts, UE4 game modding, and Memory Hooks.\n"
        "The user wants a customized Lua 5.1 script based on the real unpacked game files below.\n\n"
        f"{context_snippet}\n"
        f"USER REQUEST: {user_goal}\n\n"
        "REQUIREMENTS:\n"
        "1. Write 100% COMPLETE, VALID LUA 5.1 code (No placeholders, no pseudo-code).\n"
        "2. Hook into or use the actual function/table names listed above where relevant.\n"
        "3. Provide clean comments in English/Hinglish explaining what each hook does.\n"
        "4. Wrap the code in ```lua ... ``` markdown block."
    )
    
    response = call_ai_api(ai_prompt)
    if not response:
        console.print("[bold red]❌ AI response generate nahi ho paya. Please check internet connection / API keys.[/bold red]")
        return

    # Extract Lua code
    lua_code = response
    code_match = re.search(r'```(?:lua)?\s*(.*?)\s*```', response, re.DOTALL)
    if code_match:
        lua_code = code_match.group(1).strip()

    console.print("\n[bold bright_green]✅ AI Generated Lua Mod Script:[/bold bright_green]\n")
    console.print(Panel(escape(lua_code[:1200]) + ("\n... [truncated]" if len(lua_code) > 1200 else ""), border_style="green", box=ROUNDED))
    
    # Save script to LUA / RESULT folders
    timestamp = int(time.time())
    out_lua_name = f"mod_script_{timestamp}.lua"
    
    target_dirs = [
        data_path / "LUA",
        data_path / "RESULT",
        Path("/sdcard/FeaturesticLeaks/LUA"),
        Path("/sdcard/FeaturesticLeaks/RESULT")
    ]
    
    saved_paths = []
    for td in target_dirs:
        try:
            td.mkdir(parents=True, exist_ok=True)
            out_f = td / out_lua_name
            out_f.write_text(lua_code, encoding="utf-8")
            saved_paths.append(out_f)
        except Exception:
            pass

    console.print(f"[bold green]💾 Script saved to:[/bold green] [bright_yellow]{out_lua_name}[/bright_yellow] in LUA & RESULT folders!")

    # Offer Auto-Compile
    compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
    if compiler and saved_paths:
        do_compile = safe_input("\n⚡ Kya is script ko abhi Bytecode (.luac) me compile karun? (y/n) [y]: ").strip().lower()
        if do_compile in ['', 'y', 'yes', 'haan', '1']:
            src_f = saved_paths[0]
            out_luac = src_f.with_suffix(".luac")
            proc = subprocess.run([compiler, "-o", str(out_luac), str(src_f)], capture_output=True, text=True)
            if proc.returncode == 0:
                console.print(f"[bold green]✅ Compiled Successfully -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)![/bold green]")
                console.print(f"[bold bright_cyan]👉 Is file ko aap seedha PAK Option [2] -> Option [3] se PAK me Inject ya Repack kar sakte hain![/bold bright_cyan]\n")
            else:
                console.print(f"[bold yellow]⚠️ Compilation note: {proc.stderr.strip()}[/bold yellow]")
                
    console.print("[bold bright_green]🎉 AI Mod Generation Workflow Completed Successfully![/bold bright_green]\n")
