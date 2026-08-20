import os
import sys
import json
import time
import re
import html
import urllib.request
import ssl
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.box import ROUNDED
    from rich.markup import escape
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                print(args[0])
    class DummyPanel:
        def __init__(self, content, *args, **kwargs):
            self.content = content
        def __str__(self):
            return str(self.content)
    console = DummyConsole()
    Panel = DummyPanel
    ROUNDED = ""
    def escape(s): return str(s)

def get_device_user_info() -> str:
    try:
        from ai.assistant import get_ai_config
        cfg = get_ai_config()
        tg_uname = cfg.get("telegram_username") or cfg.get("user_nickname")
        if tg_uname:
            tg_clean = str(tg_uname).strip()
            if not tg_clean.startswith("@") and " " not in tg_clean and not tg_clean.startswith("http"):
                tg_clean = f"@{tg_clean}"
            return f"{tg_clean}"
    except Exception:
        pass
    
    u = os.environ.get("USER") or os.environ.get("LOGNAME") or os.environ.get("SUDO_USER")
    if not u:
        try:
            import getpass
            u = getpass.getuser()
        except Exception:
            u = "TermuxUser"
    try:
        import socket
        h = socket.gethostname()
    except Exception:
        h = "Android"
    return f"{u}@{h}"

def cleanup_old_logs(logs_dir: Optional[Path] = None, max_age_days: float = 2.0, max_files: int = 15):
    try:
        dirs_to_clean = []
        if logs_dir:
            dirs_to_clean.append(logs_dir)
        dirs_to_clean.extend([
            Path(__file__).parent.parent / "logs",
            Path("/sdcard/FeaturesticLeaks/ERROR_REPORTS"),
            Path("/sdcard/FeaturesticLeaks/logs")
        ])
        
        now = time.time()
        max_age_sec = max_age_days * 86400
        
        for d in set(dirs_to_clean):
            if not d.exists() or not d.is_dir():
                continue
            
            log_files = sorted([f for f in d.iterdir() if f.is_file() and (f.suffix in ['.log', '.txt'])], key=lambda x: x.stat().st_mtime, reverse=True)
            
            remaining_files = []
            for f in log_files:
                try:
                    if (now - f.stat().st_mtime) > max_age_sec:
                        f.unlink()
                    else:
                        remaining_files.append(f)
                except Exception:
                    pass
            
            if len(remaining_files) > max_files:
                for f in remaining_files[max_files:]:
                    try:
                        f.unlink()
                    except Exception:
                        pass
    except Exception:
        pass

def send_telegram_bug_report(err_type: str, err_msg: str, action_name: str = "Operation", file_info: str = "?", line_no: str = "?", func_name: str = "?", tb_str: str = "", ai_suggestion: str = ""):
    if any(k in str(err_type).upper() or k in str(err_msg).upper() for k in ["API_KEY", "EXHAUSTED", "RATE_LIMIT", "HTTP 429"]):
        if err_type != "TEST_PING":
            return

    def _send_bg():
        try:
            from ai.assistant import get_ai_config, call_ai_api
            cfg = get_ai_config()
            bot_token = cfg.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN") or "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
            chat_id = cfg.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID") or "-1004375122082"
            
            if not bot_token or not chat_id:
                return
                
            dev_user = get_device_user_info()
            
            ai_solution = ai_suggestion.strip() if (ai_suggestion and str(ai_suggestion).strip()) else ""
            if not ai_solution and err_type != "TEST_PING":
                try:
                    fix_prompt = (
                        "You are OpenCode AI Auto-Fix & Diagnostic Engine.\n"
                        "An unhandled error occurred in FeaturesticLeaks:\n"
                        f"Action: {action_name}\n"
                        f"Error Type: {err_type}\n"
                        f"Error Message: {err_msg}\n"
                        f"Location: {file_info}:{line_no} in {func_name}()\n"
                        f"Traceback:\n{tb_str[-600:] if tb_str else 'N/A'}\n\n"
                        "Analyze the exact root cause and give a clear, actionable 2-3 line fix/solution in friendly Hinglish."
                    )
                    sol = call_ai_api(fix_prompt)
                    if sol and sol.strip():
                        ai_solution = sol.strip()
                except Exception:
                    pass

            safe_user = html.escape(str(dev_user))
            safe_action = html.escape(str(action_name))
            safe_err_type = html.escape(str(err_type))
            safe_msg = html.escape(str(err_msg)[:500])
            safe_tb = html.escape(str(tb_str)[-800:]) if tb_str else "N/A"
            safe_solution = html.escape(str(ai_solution)) if ai_solution else ""

            ai_html_block = f"\n🤖 <b>AI Suggested Fix:</b>\n<code>{safe_solution}</code>\n" if safe_solution else ""

            report_html = (
                f"🚨 <b>FEATURESTIC LEAKS - CODE BUG REPORT</b> 🚨\n\n"
                f"👤 <b>User / Telegram:</b> <code>{safe_user}</code>\n"
                f"📌 <b>Action:</b> {safe_action}\n"
                f"⚠️ <b>Error Type:</b> {safe_err_type}\n"
                f"📍 <b>Location:</b> {file_info}:{line_no} in <code>{func_name}()</code>\n"
                f"💬 <b>Details:</b> <code>{safe_msg}</code>\n"
                f"{ai_html_block}\n"
                f"📜 <b>Traceback snippet:</b>\n<code>{safe_tb}</code>"
            )

            cpp_filename = f"bug_report_{re.sub(r'[^a-zA-Z0-9_]', '_', str(err_type))}.cpp"
            cpp_report_code = f"""// =====================================================================
// FEATURESTIC LEAKS - AUTOMATED BUG & DIAGNOSTIC REPORT (.cpp)
// =====================================================================
// User / Telegram : {dev_user}
// Action          : {action_name}
// Error Type      : {err_type}
// Location        : {file_info}:{line_no} in {func_name}()
// Date / Time     : {time.strftime('%Y-%m-%d %H:%M:%S')}
// =====================================================================

#include <iostream>
#include <string>

/*
[ERROR DETAILS & DESCRIPTION]
{err_msg}

[OPENCODE AI AUTO-FIX & RECOMMENDED SOLUTION]
{ai_solution if ai_solution else "No auto-solution generated."}

[TRACEBACK SNIPPET]
{tb_str if tb_str else "N/A"}
*/

void bug_report_info() {{
    std::cout << "FeaturesticLeaks Automated Bug Diagnostic Engine" << std::endl;
    std::cout << "User: {dev_user}" << std::endl;
    std::cout << "Error: {err_type}" << std::endl;
}}
"""

            doc_caption = (
                f"🚨 <b>BUG REPORT (.cpp File Attached)</b> 🚨\n\n"
                f"👤 <b>User:</b> <code>{safe_user}</code>\n"
                f"📌 <b>Action:</b> {safe_action}\n"
                f"⚠️ <b>Error Type:</b> {safe_err_type}\n"
                f"📍 <b>Location:</b> {file_info}:{line_no} in <code>{func_name}()</code>\n"
                f"📎 <b>Attached File:</b> <code>{cpp_filename}</code>"
            )

            doc_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            try:
                import requests
                files = {
                    'document': (cpp_filename, cpp_report_code.encode('utf-8'), 'text/x-c++src')
                }
                data = {
                    'chat_id': chat_id,
                    'caption': doc_caption,
                    'parse_mode': 'HTML'
                }
                r_doc = requests.post(doc_url, data=data, files=files, timeout=10)
                if r_doc.status_code == 200:
                    return
            except Exception:
                pass

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            try:
                boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
                body = []
                body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode('utf-8'))
                body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{doc_caption}\r\n'.encode('utf-8'))
                body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n'.encode('utf-8'))
                body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{cpp_filename}"\r\nContent-Type: text/x-c++src\r\n\r\n'.encode('utf-8'))
                body.append(cpp_report_code.encode('utf-8'))
                body.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
                payload_doc = b''.join(body)

                req_doc = urllib.request.Request(
                    doc_url,
                    data=payload_doc,
                    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
                )
                urllib.request.urlopen(req_doc, timeout=10, context=ssl_ctx)
                return
            except Exception:
                pass

            payload_html = json.dumps({
                "chat_id": chat_id,
                "text": report_html,
                "parse_mode": "HTML"
            }).encode("utf-8")
            
            try:
                req = urllib.request.Request(msg_url, data=payload_html, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=8, context=ssl_ctx)
            except Exception:
                pass
        except Exception:
            pass

    import threading
    threading.Thread(target=_send_bg, daemon=True).start()

def send_telegram_status_update(action_name: str, status_msg: str, file_details: str = ""):
    def _send_bg():
        try:
            from ai.assistant import get_ai_config
            cfg = get_ai_config()
            bot_token = cfg.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN") or "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
            chat_id = cfg.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID") or "-1004375122082"
            
            if not bot_token or not chat_id:
                return
                
            dev_user = get_device_user_info()
            safe_user = html.escape(str(dev_user))
            safe_action = html.escape(str(action_name))
            safe_msg = html.escape(str(status_msg))
            safe_files = html.escape(str(file_details)) if file_details else "N/A"

            report_html = (
                f"✅ <b>FEATURESTIC LEAKS - ACTION COMPLETED</b> ✅\n\n"
                f"👤 <b>User / Telegram:</b> <code>{safe_user}</code>\n"
                f"📌 <b>Action:</b> {safe_action}\n"
                f"💬 <b>Status:</b> <code>{safe_msg}</code>\n"
                f"📁 <b>Files:</b> <code>{safe_files}</code>"
            )

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            try:
                import requests
                requests.post(url, json={"chat_id": chat_id, "text": report_html, "parse_mode": "HTML"}, timeout=6)
                return
            except Exception:
                pass

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            payload = json.dumps({"chat_id": chat_id, "text": report_html, "parse_mode": "HTML"}).encode("utf-8")
            try:
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=6, context=ssl_ctx)
            except Exception:
                pass
        except Exception:
            pass

    import threading
    threading.Thread(target=_send_bg, daemon=True).start()

def handle_exception(e: Exception, action_name: str = "Operation", data_path: Optional[Path] = None):
    err_type = type(e).__name__
    raw_msg = str(e).strip() if (str(e) and str(e).strip()) else ""
    
    if not raw_msg:
        if err_type == "AssertionError":
            err_msg = "Invalid PAK header/structure or verification check failed"
        elif err_type == "ValueError":
            err_msg = "Invalid value or unsupported PAK version"
        elif err_type == "KeyError":
            err_msg = "Target file or path key not found in PAK index"
        else:
            err_msg = f"{err_type} occurred without additional details"
    else:
        err_msg = raw_msg

    tb_lines = traceback.extract_tb(e.__traceback__)
    file_info = "FeaturesticLeaks.py"
    line_no = "?"
    func_name = action_name
    
    if tb_lines:
        last_frame = tb_lines[-1]
        file_info = Path(last_frame.filename).name
        line_no = str(last_frame.lineno)
        func_name = last_frame.name

    is_file_issue = False
    
    if isinstance(e, (FileNotFoundError, PermissionError, IsADirectoryError, MemoryError, EOFError, struct.error)):
        is_file_issue = True
    elif isinstance(e, OSError) and ("no space" in err_msg.lower() or getattr(e, 'errno', None) in (28, 13, 2)):
        is_file_issue = True
    elif any(term in err_type.lower() for term in ["badzip", "zlib", "zstd", "compression", "struct", "error"]):
        if any(kw in err_msg.lower() for kw in ["unpack", "buffer", "offset", "magic", "header", "truncate", "corrupt", "bytes"]):
            is_file_issue = True
    elif isinstance(e, (AssertionError, ValueError, KeyError, IndexError)):
        file_keywords = [
            "pak", "header", "magic", "version", "corrupt", "index", "zlib", "zstd",
            "lz4", "encrypted", "signature", "decompression", "truncated", "uasset",
            "luac", "bytecode", "syntax", "not found", "invalid file", "bad format",
            "size", "entry", "offset", "file", "directory", "folder", "path", "does not exist",
            "0 byte", "empty", "read error", "write error", "mount", "unsupported"
        ]
        if any(kw in err_msg.lower() for kw in file_keywords) or not err_msg:
            is_file_issue = True

    if is_file_issue:
        category_header = "[bold bright_yellow]📂 USER FILE / INPUT ISSUE[/bold bright_yellow]"
        category_border = "yellow"
        diagnosis = (
            "[bold yellow]⚠️ Diagnostic Result:[/bold yellow] [bold white]Yeh issue AAPKI INPUT FILE / PATH me hai.[/bold white]\n"
            "[dim]Tool bilkul Sahi (OK) kaam kar raha hai. Aapki input file corrupt ho sakti hai, missing ho sakti hai, ya wrong format me hai.[/dim]"
        )
    else:
        category_header = "[bold bright_red]🛠️ TOOL INTERNAL BUG / CODE ISSUE[/bold bright_red]"
        category_border = "bold red"
        diagnosis = (
            "[bold red]❌ Diagnostic Result:[/bold red] [bold white]Yeh TOOL ka Internal Code Bug / System Issue hai![/bold white]\n"
            "[bold bright_cyan]👉 Help / Bug Resolution ke liye Developer se Telegram par contact karein:[/bold bright_cyan] [bold bright_yellow]@L359D[/bold bright_yellow]"
        )

    hint_msg = ""
    if isinstance(e, PermissionError):
        hint_msg = "Folder access denied. File ko `/sdcard/Download/` me copy karke try karein, ya storage permission grant karein."
    elif isinstance(e, FileNotFoundError):
        hint_msg = "File ya folder nahi mila. Path spelling aur SDCard location check karein."
    elif isinstance(e, MemoryError) or "out of memory" in err_msg.lower():
        hint_msg = "RAM Limit exceed ho gayi. Background apps close karein aur chhotey files try karein."
    elif isinstance(e, OSError) and ("no space" in err_msg.lower() or getattr(e, 'errno', None) == 28):
        hint_msg = "Storage full hai. Internal memory me space free karke retry karein."
    elif any(term in err_type.lower() or term in err_msg.lower() for term in ["zlib", "zstd", "decompress", "compress", "badzip"]):
        hint_msg = "File corrupt hai ya unsupported compression/encryption format hai."
    elif any(term in err_msg.lower() for term in ["buffer", "unpack", "struct", "truncated", "too small", "underflow"]):
        hint_msg = "PAK/OBB file incomplete/truncated hai ya size 45 bytes se chhota hai. Please complete original .pak file use karein."
    elif "magic" in err_msg.lower() or "header" in err_msg.lower() or "version" in err_msg.lower():
        hint_msg = "File ka PAK/OBB Header mismatch ho raha hai. File corrupt ya password protected/encrypted ho sakti hai."
    elif is_file_issue:
        hint_msg = "Check karein ki file `/sdcard/FeaturesticLeaks/` folder me proper format me present hai."

    log_filename = "N/A"
    try:
        base = data_path if data_path else Path(__file__).parent.parent
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        cleanup_old_logs(logs_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"error_{timestamp}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Category: {'USER_FILE_ISSUE' if is_file_issue else 'TOOL_BUG'}\n")
            f.write(f"Action: {action_name}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Error Type: {err_type}\n")
            f.write(f"Error Message: {err_msg}\n")
            f.write(f"Location: {file_info}:{line_no} in {func_name}()\n\n")
            f.write("Full Traceback:\n")
            f.write(traceback.format_exc())
            
        log_filename = f"logs/{log_file.name}"
    except Exception:
        pass

    ai_live_fix = ""
    try:
        from ai.assistant import call_ai_api
        sol = call_ai_api(
            f"User ran into an error in FeaturesticLeaks during action '{action_name}':\n"
            f"Error: {err_type}: {err_msg}\n"
            f"Location: {file_info}:{line_no} in {func_name}()\n"
            "Give a short 1-2 line direct solution in Hinglish telling the user exactly how to fix or bypass this issue right now so they can continue working."
        )
        if sol and sol.strip():
            ai_live_fix = sol.strip()
    except Exception:
        pass

    if not is_file_issue and not any(k in str(err_type).upper() or k in str(err_msg).upper() for k in ["API_KEY", "EXHAUSTED", "RATE_LIMIT"]):
        try:
            send_telegram_bug_report(
                err_type,
                err_msg,
                action_name,
                file_info,
                str(line_no),
                func_name,
                traceback.format_exc(),
                ai_suggestion=ai_live_fix
            )
        except Exception:
            pass

    panel_content = (
        f"[dim]Category:[/dim] {category_header}\n"
        f"{diagnosis}\n\n"
        f"[dim]Operation:[/dim] [cyan]{escape(action_name)}[/cyan]\n"
        f"[dim]Error Details:[/dim] [bold red]{escape(err_type)}[/bold red] in [bold yellow]{escape(func_name)}()[/bold yellow] ([cyan]{escape(file_info)}[/cyan]:[yellow]{line_no}[/yellow])\n"
        f"[dim]Message:[/dim] {escape(err_msg)}"
    )
    if ai_live_fix:
        panel_content += f"\n[bold bright_cyan]🤖 OpenCode AI Auto-Fix Solution:[/bold bright_cyan] [bold white]{escape(ai_live_fix)}[/bold white]"
    elif hint_msg:
        panel_content += f"\n[bold yellow]💡 Solution Tip:[/bold yellow] [white]{escape(hint_msg)}[/white]"
    
    panel_content += f"\n[dim]Saved Log:[/dim] [dim cyan]{escape(log_filename)}[/dim cyan]"

    error_panel = Panel(
        panel_content,
        title="[bold red] 🚨 DIAGNOSTIC ERROR REPORT 🚨 [/bold red]",
        title_align="left",
        border_style=category_border,
        box=ROUNDED,
        padding=(1, 2)
    )
    
    console.print()
    console.print(error_panel)
