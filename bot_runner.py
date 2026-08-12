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
import traceback
import urllib.request
import urllib.parse
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

# Telegram Bot Token & Chat ID resolution
def get_bot_credentials():
    try:
        cfg = get_ai_config()
    except Exception:
        cfg = {}
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_bot_token") or "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or cfg.get("telegram_chat_id") or "-1004375122082"
    return token.strip(), chat_id.strip()

BOT_TOKEN, TARGET_CHAT_ID = get_bot_credentials()
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_msg(text, chat_id=None, parse_mode="HTML"):
    if not chat_id:
        chat_id = TARGET_CHAT_ID
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": parse_mode}).encode('utf-8')
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Telegram Send Error: {e}")
        return None

def send_telegram_document(file_path: Path, caption="", chat_id=None):
    if not chat_id:
        chat_id = TARGET_CHAT_ID
    if not file_path.exists():
        return
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        print(f"Send Document Error: {e}")

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
    msg = update.get("message") or update.get("channel_post")
    if not msg:
        return
    
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or msg.get("caption") or "").strip()

    # Handle Uploaded Document/Files
    if "document" in msg:
        doc = msg["document"]
        file_name = doc.get("file_name", "uploaded_file")
        file_id = doc.get("file_id")
        ext = Path(file_name).suffix.lower()

        send_telegram_msg(f"📥 <b>Received File:</b> <code>{file_name}</code>\nProcessing file in workspace...", chat_id=chat_id)

        if ext in [".pak", ".obb"]:
            save_path = data_path / "PAK" / file_name
            if download_telegram_file(file_id, save_path):
                send_telegram_msg(f"✅ Saved <code>{file_name}</code> to <b>PAK/</b> folder.\nAttempting automatic unpack...", chat_id=chat_id)
                unpack_out = data_path / "UNPACK" / save_path.stem
                try:
                    repack_pak_file_full(save_path, unpack_out, None)
                    send_telegram_msg(f"🎉 <b>Unpack Successful!</b>\nFolder: <code>UNPACK/{save_path.stem}</code>", chat_id=chat_id)
                except Exception as ex:
                    send_telegram_msg(f"❌ <b>Unpack Error:</b> {ex}", chat_id=chat_id)
        elif ext in [".lua", ".luac"]:
            save_path = data_path / "LUA" / file_name
            if download_telegram_file(file_id, save_path):
                send_telegram_msg(f"✅ Saved <code>{file_name}</code> to <b>LUA/</b> folder.\nAuto-fixing & compiling script...", chat_id=chat_id)
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
                    send_telegram_msg(f"❌ <b>Process Error:</b> {ex}", chat_id=chat_id)
        else:
            save_path = data_path / "INPUT" / file_name
            if download_telegram_file(file_id, save_path):
                send_telegram_msg(f"✅ Saved file to <b>INPUT/</b> folder: <code>{file_name}</code>", chat_id=chat_id)
        return

    if not text:
        return

    low_text = text.lower()

    if low_text.startswith("/start") or low_text.startswith("/help"):
        help_msg = (
            "⚡ <b>FEATURESTIC LEAKS - 24/7 BOT SERVICE</b> ⚡\n\n"
            "<b>Available Bot Commands:</b>\n"
            "• <code>/status</code> - Show workspace status & live file snapshot\n"
            "• <code>/ai &lt;query&gt;</code> - Ask OpenCode AI assistant\n"
            "• <code>/unpack</code> - Unpack PAK/OBB files in PAK/ folder\n"
            "• <code>/repack</code> - Repack files from UNPACK/ or RESULT/\n"
            "• <code>/compile</code> - Compile Lua scripts in LUA/ folder\n"
            "• <code>/clean</code> - Clear all temporary workspace folders\n"
            "• <code>/restart</code> - Restart bot instance loop\n\n"
            "💡 <b>Tip:</b> Direct send any <code>.pak</code>, <code>.obb</code>, <code>.lua</code> or <code>.luac</code> file to auto-process!"
        )
        send_telegram_msg(help_msg, chat_id=chat_id)

    elif low_text.startswith("/status") or low_text.startswith("/workspace"):
        try:
            snapshot = get_live_workspace_context(data_path)
            send_telegram_msg(f"📊 <b>WORKSPACE LIVE SNAPSHOT:</b>\n<pre>{html.escape(snapshot)}</pre>", chat_id=chat_id)
        except Exception as e:
            send_telegram_msg(f"Error fetching status: {e}", chat_id=chat_id)

    elif low_text.startswith("/ai "):
        prompt = text[4:].strip()
        send_telegram_msg("🤖 <i>OpenCode AI is thinking...</i>", chat_id=chat_id)
        try:
            ans = call_ai_api(prompt)
            send_telegram_msg(f"🤖 <b>OpenCode AI Answer:</b>\n{html.escape(ans)}", chat_id=chat_id)
        except Exception as e:
            send_telegram_msg(f"❌ AI Call Error: {e}", chat_id=chat_id)

    elif low_text.startswith("/clean"):
        deleted = 0
        for d in [data_path / "INPUT", data_path / "OUTPUT", data_path / "UNPACK", data_path / "REPACK", data_path / "RESULT", data_path / "TEMP_INJECT"]:
            if d.exists():
                for f in d.iterdir():
                    try:
                        if f.is_file(): f.unlink()
                        elif f.is_dir(): import shutil; shutil.rmtree(f, ignore_errors=True)
                        deleted += 1
                    except Exception: pass
        send_telegram_msg(f"🧹 <b>Workspace Cleaned!</b> Removed {deleted} file(s)/folder(s).", chat_id=chat_id)

    elif low_text.startswith("/restart"):
        send_telegram_msg("🔄 <b>Manual Restart Initiated!</b> Restarting runner instance...", chat_id=chat_id)
        trigger_github_restart()
        sys.exit(0)

def main():
    start_time = time.time()
    user_info = get_device_user_info()
    
    init_banner = (
        "🚀 <b>FEATURESTIC LEAKS BOT ONLINE!</b> 🚀\n\n"
        f"👤 <b>Runner Host:</b> <code>{html.escape(user_info)}</code>\n"
        f"⏱️ <b>Safety Timer:</b> 5 Hours 50 Minutes (21,000s)\n"
        "🟢 Status: Active Long-Polling Listener 24/7"
    )
    send_telegram_msg(init_banner)
    print("FeaturesticLeaks Bot long-polling started...")

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
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    main()
