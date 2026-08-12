#!/usr/bin/env python3
"""
24/7 FeaturesticLeaks Telegram Bot Engine & Continuous Workflow Runner
Runs long polling for Telegram Bot commands & automated workspace processing.
Auto-restarts via GitHub Repository Dispatch at 5h 50m (21,000s) execution limit.
"""

import os
import sys
import time
import json
import html
import shutil
import traceback
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# Workspace Setup
BASE_DIR = Path(__file__).parent.resolve()
data_path = Path("/sdcard/FeaturesticLeaks") if Path("/sdcard").exists() else BASE_DIR

# Ensure workspace directories
for d in ["INPUT", "OUTPUT", "UNPACK", "REPACK", "RESULT", "TEMP_INJECT", "PAK", "LUA", "INJECT"]:
    (data_path / d).mkdir(parents=True, exist_ok=True)

# Imports from core and FeaturesticLeaks modules
sys.path.insert(0, str(BASE_DIR))

try:
    from core.logging_utils import get_device_user_info, send_telegram_status_update
    from FeaturesticLeaks import (
        get_ai_config, call_ai_api,
        ai_fix_lua_code,
        get_live_workspace_context,
        ensure_directories
    )
    from pak.repack import repack_pak_file_full, detect_repack_mode
    from lua.tools import run_lua_compiler, run_lua_decompiler, fix_lua_syntax_for_lua51
except Exception as e:
    print(f"Warning/Error loading submodules: {e}")

# Continuous Execution Limit: 5 hours 50 minutes (350 minutes = 21,000 seconds)
MAX_RUN_TIME = 350 * 60

def human_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

# Telegram Bot Token & Chat ID resolution
def get_bot_credentials():
    try:
        cfg = get_ai_config()
    except Exception:
        cfg = {}
    
    token = os.environ.get("RUNNER_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("runner_bot_token") or cfg.get("telegram_bot_token") or "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
    chat_id = os.environ.get("RUNNER_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or cfg.get("runner_chat_id") or cfg.get("telegram_chat_id") or "-1004375122082"
    return token.strip(), chat_id.strip()

BOT_TOKEN, TARGET_CHAT_ID = get_bot_credentials()
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_msg(text, chat_id=None, parse_mode="HTML"):
    if not chat_id:
        chat_id = TARGET_CHAT_ID
    if not chat_id or not BOT_TOKEN:
        print("[Warning] Cannot send msg: BOT_TOKEN or chat_id is missing.")
        return None

    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": parse_mode}).encode('utf-8')
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except urllib.error.HTTPError as http_err:
        print(f"Telegram Send HTTPError ({http_err.code}): {http_err.reason}. Retrying as plain text...")
        try:
            plain_payload = json.dumps({"chat_id": chat_id, "text": text}).encode('utf-8')
            req = urllib.request.Request(url, data=plain_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read()
        except Exception as ex:
            print(f"Telegram Send Plain Fallback Error: {ex}")
            return None
    except Exception as e:
        print(f"Telegram Send Error: {e}")
        return None

def send_telegram_document(file_path: Path, caption="", chat_id=None):
    if not chat_id:
        chat_id = TARGET_CHAT_ID
    if not chat_id or not BOT_TOKEN or not file_path.exists():
        return None

    url = f"{TELEGRAM_API_URL}/sendDocument"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    body = []
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode('utf-8'))
    if caption:
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode('utf-8'))
    
    filename = file_path.name
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode('utf-8'))
    body.append(file_path.read_bytes())
    body.append(f"\r\n--{boundary}--\r\n".encode('utf-8'))
    
    payload = b''.join(body)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        print(f"Send Document Error: {e}")
        send_telegram_msg(f"📁 Processed file <code>{html.escape(file_path.name)}</code> ({human_size(file_path.stat().st_size)}) saved in workspace, but upload failed.", chat_id=chat_id)
        return None

def trigger_github_restart():
    gh_pat = os.environ.get("GH_PAT_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not gh_pat or not repo:
        print("GH_PAT_TOKEN or GITHUB_REPOSITORY not configured. Skipping auto-dispatch.")
        return False
    
    url = f"https://api.github.com/repos/{repo}/dispatches"
    payload = json.dumps({"event_type": "restart_bot"}).encode('utf-8')
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {gh_pat}",
        "Content-Type": "application/json",
        "User-Agent": "FeaturesticLeaks-Bot"
    }
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("Successfully triggered GitHub Actions restart dispatch.")
            return True
    except Exception as e:
        print(f"GitHub Dispatch Error: {e}")
        return False

def download_telegram_file(file_id: str, dest_path: Path) -> bool:
    try:
        get_file_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
        req = urllib.request.Request(get_file_url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if not res_data.get("ok"):
                return False
            file_path_str = res_data["result"]["file_path"]
        
        dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_str}"
        with urllib.request.urlopen(dl_url, timeout=60) as dl_resp:
            dest_path.write_bytes(dl_resp.read())
        return True
    except Exception as e:
        print(f"Download Error: {e}")
        return False

def handle_incoming_update(update):
    try:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return
        
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            return

        text = (msg.get("text") or msg.get("caption") or "").strip()

        # Handle Uploaded Documents / Files
        if "document" in msg:
            doc = msg["document"]
            file_name = doc.get("file_name", "uploaded_file")
            file_id = doc.get("file_id")
            ext = Path(file_name).suffix.lower()

            send_telegram_msg(f"📥 <b>Received File:</b> <code>{html.escape(file_name)}</code>\nProcessing file in workspace...", chat_id=chat_id)

            if ext in [".pak", ".obb"]:
                save_path = data_path / "PAK" / file_name
                if download_telegram_file(file_id, save_path):
                    send_telegram_msg(f"✅ Saved <code>{html.escape(file_name)}</code> to <b>PAK/</b> folder.\nAttempting automatic unpack...", chat_id=chat_id)
                    unpack_out = data_path / "UNPACK" / save_path.stem
                    try:
                        repack_pak_file_full(save_path, unpack_out, None)
                        send_telegram_msg(f"🎉 <b>Unpack Successful!</b>\nFolder: <code>UNPACK/{html.escape(save_path.stem)}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ <b>Unpack Error:</b> {html.escape(str(ex))}", chat_id=chat_id)
            elif ext in [".lua", ".luac"]:
                save_path = data_path / "LUA" / file_name
                if download_telegram_file(file_id, save_path):
                    send_telegram_msg(f"✅ Saved <code>{html.escape(file_name)}</code> to <b>LUA/</b> folder.\nAuto-fixing & compiling script...", chat_id=chat_id)
                    try:
                        raw_code = save_path.read_text(encoding="utf-8", errors="ignore")
                        fixed = fix_lua_syntax_for_lua51(raw_code)
                        out_luac = data_path / "RESULT" / (save_path.stem + ".luac")
                        comp_ok, comp_msg = run_lua_compiler(save_path, out_luac)
                        if comp_ok and out_luac.exists():
                            send_telegram_document(out_luac, caption=f"✅ <b>Lua Auto-Compile Complete!</b>\n{out_luac.name}", chat_id=chat_id)
                        else:
                            send_telegram_msg(f"⚠️ <b>Compile Warning/Error:</b>\n<code>{html.escape(comp_msg[:500])}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ <b>Process Error:</b> {html.escape(str(ex))}", chat_id=chat_id)
            else:
                save_path = data_path / "INPUT" / file_name
                if download_telegram_file(file_id, save_path):
                    send_telegram_msg(f"✅ Saved file to <b>INPUT/</b> folder: <code>{html.escape(file_name)}</code>", chat_id=chat_id)
            return

        if not text:
            return

        # Clean command and handle group mentions (e.g. /start@BotUsername -> /start)
        first_word = text.split()[0].lower() if text else ""
        cmd_clean = first_word.split('@')[0] if '@' in first_word else first_word

        if cmd_clean in ["/start", "/help"]:
            help_msg = (
                "⚡ <b>FEATURESTIC LEAKS - 24/7 BOT SERVICE</b> ⚡\n\n"
                "<b>Available Bot Commands:</b>\n"
                "• <code>/status</code> - Show workspace status & live file snapshot\n"
                "• <code>/unpack</code> - Auto unpack PAK/OBB files in PAK/ folder\n"
                "• <code>/repack</code> - Auto repack folders from UNPACK/ into PAK\n"
                "• <code>/compile</code> - Auto compile Lua scripts in LUA/ folder\n"
                "• <code>/ai &lt;query&gt;</code> - Ask OpenCode AI assistant\n"
                "• <code>/clean</code> - Clear all temporary workspace folders\n"
                "• <code>/restart</code> - Restart bot runner instance\n\n"
                "💡 <b>Tip:</b> Simply upload any <code>.pak</code>, <code>.obb</code>, or <code>.lua</code> file directly to auto-process!"
            )
            send_telegram_msg(help_msg, chat_id=chat_id)

        elif cmd_clean in ["/status", "/workspace"]:
            try:
                snapshot = get_live_workspace_context(data_path)
                send_telegram_msg(f"📊 <b>WORKSPACE LIVE SNAPSHOT:</b>\n<pre>{html.escape(snapshot)}</pre>", chat_id=chat_id)
            except Exception as e:
                send_telegram_msg(f"Error fetching status: {html.escape(str(e))}", chat_id=chat_id)

        elif cmd_clean == "/unpack":
            pak_files = [f for f in (data_path / "PAK").glob("*.*") if f.suffix.lower() in [".pak", ".obb"]]
            if not pak_files:
                send_telegram_msg("📦 <b>No PAK/OBB files found in PAK/ folder.</b>\nPlease upload a <code>.pak</code> or <code>.obb</code> file first!", chat_id=chat_id)
            else:
                for pf in pak_files:
                    send_telegram_msg(f"⏳ Unpacking <code>{html.escape(pf.name)}</code>...", chat_id=chat_id)
                    unpack_out = data_path / "UNPACK" / pf.stem
                    try:
                        repack_pak_file_full(pf, unpack_out, None)
                        send_telegram_msg(f"🎉 <b>Unpack Successful!</b>\nFolder: <code>UNPACK/{html.escape(pf.stem)}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ Unpack error on {html.escape(pf.name)}: {html.escape(str(ex))}", chat_id=chat_id)

        elif cmd_clean == "/repack":
            unpack_dirs = [d for d in (data_path / "UNPACK").iterdir() if d.is_dir()]
            if not unpack_dirs:
                send_telegram_msg("📦 <b>No unpacked folders found in UNPACK/!</b>\nPlease upload or unpack a PAK file first.", chat_id=chat_id)
            else:
                for ud in unpack_dirs:
                    out_pak = data_path / "RESULT" / f"repacked_{ud.name}.pak"
                    send_telegram_msg(f"⏳ Repacking folder <code>UNPACK/{html.escape(ud.name)}</code>...", chat_id=chat_id)
                    try:
                        repack_pak_file_full(None, ud, out_pak)
                        if out_pak.exists():
                            send_telegram_document(out_pak, caption=f"✅ <b>Repacked PAK File Ready!</b>\n{out_pak.name}", chat_id=chat_id)
                        else:
                            send_telegram_msg(f"❌ Repack failed for {html.escape(ud.name)}.", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ Repack error on {html.escape(ud.name)}: {html.escape(str(ex))}", chat_id=chat_id)

        elif cmd_clean == "/compile":
            lua_files = [f for f in (data_path / "LUA").glob("*.*") if f.suffix.lower() in [".lua", ".txt"]]
            if not lua_files:
                send_telegram_msg("📜 <b>No Lua files found in LUA/ folder.</b>\nPlease upload a <code>.lua</code> script first!", chat_id=chat_id)
            else:
                for lf in lua_files:
                    send_telegram_msg(f"⏳ Compiling <code>{html.escape(lf.name)}</code>...", chat_id=chat_id)
                    try:
                        raw_code = lf.read_text(encoding="utf-8", errors="ignore")
                        fixed = fix_lua_syntax_for_lua51(raw_code)
                        out_luac = data_path / "RESULT" / (lf.stem + ".luac")
                        comp_ok, comp_msg = run_lua_compiler(lf, out_luac)
                        if comp_ok and out_luac.exists():
                            send_telegram_document(out_luac, caption=f"✅ <b>Lua Auto-Compile Complete!</b>\n{out_luac.name}", chat_id=chat_id)
                        else:
                            send_telegram_msg(f"⚠️ <b>Compile Error:</b>\n<code>{html.escape(comp_msg[:500])}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ Compile error on {html.escape(lf.name)}: {html.escape(str(ex))}", chat_id=chat_id)

        elif cmd_clean == "/ai":
            prompt = text[4:].strip() if len(text) > 3 else ""
            if not prompt:
                send_telegram_msg("💡 <b>Usage:</b> <code>/ai &lt;your question&gt;</code>", chat_id=chat_id)
            else:
                send_telegram_msg("🤖 <i>OpenCode AI is thinking...</i>", chat_id=chat_id)
                try:
                    ans = call_ai_api(prompt)
                    send_telegram_msg(f"🤖 <b>OpenCode AI Answer:</b>\n{html.escape(ans)}", chat_id=chat_id)
                except Exception as e:
                    send_telegram_msg(f"❌ AI Call Error: {html.escape(str(e))}", chat_id=chat_id)

        elif cmd_clean == "/clean":
            deleted = 0
            for d in [data_path / "INPUT", data_path / "OUTPUT", data_path / "UNPACK", data_path / "REPACK", data_path / "RESULT", data_path / "TEMP_INJECT"]:
                if d.exists():
                    for f in d.iterdir():
                        try:
                            if f.is_file(): f.unlink()
                            elif f.is_dir(): shutil.rmtree(f, ignore_errors=True)
                            deleted += 1
                        except Exception: pass
            send_telegram_msg(f"🧹 <b>Workspace Cleaned!</b> Removed {deleted} file(s)/folder(s).", chat_id=chat_id)

        elif cmd_clean == "/restart":
            send_telegram_msg("🔄 <b>Manual Restart Initiated!</b> Restarting runner instance...", chat_id=chat_id)
            trigger_github_restart()
            sys.exit(0)

        else:
            # Fallback: Respond to any other message using OpenCode AI!
            send_telegram_msg("🤖 <i>OpenCode AI is thinking...</i>", chat_id=chat_id)
            try:
                ans = call_ai_api(text)
                send_telegram_msg(f"🤖 <b>OpenCode AI Answer:</b>\n{html.escape(ans)}", chat_id=chat_id)
            except Exception as e:
                send_telegram_msg(f"❌ AI Answer Error: {html.escape(str(e))}", chat_id=chat_id)

    except Exception as general_ex:
        print(f"Error handling update: {general_ex}\n{traceback.format_exc()}")
        try:
            if chat_id:
                send_telegram_msg(f"⚠️ <b>Processing Error:</b> {html.escape(str(general_ex))}", chat_id=chat_id)
        except Exception:
            pass

def main():
    start_time = time.time()
    user_info = get_device_user_info()
    
    if not BOT_TOKEN:
        print("❌ CRITICAL: No Telegram Bot Token configured! Bot cannot start.")
        sys.exit(1)

    init_banner = (
        "🚀 <b>FEATURESTIC LEAKS BOT ONLINE!</b> 🚀\n\n"
        f"👤 <b>Runner Host:</b> <code>{html.escape(user_info)}</code>\n"
        f"⏱️ <b>Safety Timer:</b> 5 Hours 50 Minutes (21,000s)\n"
        "🟢 Status: Active Long-Polling Listener 24/7"
    )
    send_telegram_msg(init_banner)
    print("FeaturesticLeaks Bot long-polling started successfully...")

    last_update_id = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed >= MAX_RUN_TIME:
            print("\n⏰ 5h 50m timer reached! Restarting runner loop...")
            send_telegram_msg("⏳ <b>5h 50m Limit Reached!</b>\nRestarting GitHub Actions workflow runner loop for continuous 24/7 uptime... 🔄")
            trigger_github_restart()
            break

        try:
            url = f"{TELEGRAM_API_URL}/getUpdates?offset={last_update_id + 1}&timeout=20"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("ok"):
                    for update in data.get("result", []):
                        last_update_id = update["update_id"]
                        handle_incoming_update(update)
                else:
                    print(f"Telegram getUpdates response error: {data}")
                    time.sleep(3)
        except urllib.error.HTTPError as http_err:
            print(f"Polling HTTPError ({http_err.code}): {http_err.reason}")
            time.sleep(5)
        except Exception as e:
            print(f"Polling Exception: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
