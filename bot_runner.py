#!/usr/bin/env python3
"""
24/7 FeaturesticLeaks Telegram Bot Engine & Continuous Workflow Runner
Runs long polling for Telegram Bot commands, Inline Keyboard Buttons, & automated workspace processing.
Supports per-user OpenCode API Key storage (/setkey) so every user can use their own API key!
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

USER_KEYS_FILE = data_path / "user_opencode_keys.json"

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

# Per-User OpenCode API Key Manager
def load_user_keys() -> dict:
    if USER_KEYS_FILE.exists():
        try:
            return json.loads(USER_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_user_key(user_id: str, api_key: str):
    keys = load_user_keys()
    keys[str(user_id)] = api_key.strip()
    USER_KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")

def get_user_key(user_id: str) -> str:
    keys = load_user_keys()
    return keys.get(str(user_id), "").strip()

# Telegram Bot Credentials
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

def send_telegram_msg(text, chat_id=None, reply_markup=None, parse_mode="HTML"):
    if not chat_id:
        chat_id = TARGET_CHAT_ID
    if not chat_id or not BOT_TOKEN:
        print("[Warning] Cannot send msg: BOT_TOKEN or chat_id is missing.")
        return None

    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload_dict = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload_dict["reply_markup"] = reply_markup

    payload = json.dumps(payload_dict).encode('utf-8')
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except urllib.error.HTTPError as http_err:
        print(f"Telegram Send HTTPError ({http_err.code}): {http_err.reason}. Retrying as plain text...")
        try:
            payload_dict.pop("parse_mode", None)
            plain_payload = json.dumps(payload_dict).encode('utf-8')
            req = urllib.request.Request(url, data=plain_payload, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read()
        except Exception as ex:
            print(f"Telegram Send Plain Fallback Error: {ex}")
            return None
    except Exception as e:
        print(f"Telegram Send Error: {e}")
        return None

def answer_callback_query(callback_query_id, text=""):
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    payload = json.dumps({"callback_query_id": callback_query_id, "text": text}).encode('utf-8')
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()
    except Exception as e:
        print(f"Answer Callback Error: {e}")

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

def download_telegram_file(file_id: str, dest_path: Path):
    try:
        get_file_url = f"{TELEGRAM_API_URL}/getFile?file_id={file_id}"
        req = urllib.request.Request(get_file_url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if not res_data.get("ok"):
                desc = res_data.get("description", "Unknown Telegram API error")
                return False, desc
            file_path_str = res_data["result"]["file_path"]
        
        dl_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_str}"
        with urllib.request.urlopen(dl_url, timeout=60) as dl_resp:
            dest_path.write_bytes(dl_resp.read())
        return True, "Success"
    except Exception as e:
        print(f"Download Error: {e}")
        return False, str(e)

def get_main_keyboard_markup():
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Workspace Status", "callback_data": "btn_status"},
                {"text": "📦 Unpack PAK/OBB", "callback_data": "btn_unpack"}
            ],
            [
                {"text": "📦 Repack PAK", "callback_data": "btn_repack"},
                {"text": "📜 Compile Lua", "callback_data": "btn_compile"}
            ],
            [
                {"text": "🔑 Set My OpenCode Key", "callback_data": "btn_setkey"},
                {"text": "🧹 Clean Workspace", "callback_data": "btn_clean"}
            ],
            [
                {"text": "🤖 AI Help / Query", "callback_data": "btn_ai_help"},
                {"text": "🔄 Restart Bot", "callback_data": "btn_restart"}
            ]
        ]
    }

def handle_incoming_update(update):
    try:
        # 1. Handle Inline Button Click (callback_query)
        if "callback_query" in update:
            cq = update["callback_query"]
            cq_id = cq["id"]
            data = cq.get("data", "")
            msg = cq.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            from_user = cq.get("from", {})
            user_id = from_user.get("id", chat_id)

            answer_callback_query(cq_id, text="Processing command...")

            if data == "btn_status":
                try:
                    snapshot = get_live_workspace_context(data_path)
                    send_telegram_msg(f"📊 <b>WORKSPACE LIVE SNAPSHOT:</b>\n<pre>{html.escape(snapshot)}</pre>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
                except Exception as e:
                    send_telegram_msg(f"Error fetching status: {html.escape(str(e))}", chat_id=chat_id)

            elif data == "btn_unpack":
                pak_files = [f for f in (data_path / "PAK").glob("*.*") if f.suffix.lower() in [".pak", ".obb"]]
                if not pak_files:
                    send_telegram_msg("📦 <b>No PAK/OBB files found in PAK/ folder.</b>\nPlease upload a <code>.pak</code> or <code>.obb</code> file first!", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
                else:
                    for pf in pak_files:
                        send_telegram_msg(f"⏳ Unpacking <code>{html.escape(pf.name)}</code>...", chat_id=chat_id)
                        unpack_out = data_path / "UNPACK" / pf.stem
                        try:
                            repack_pak_file_full(pf, unpack_out, None)
                            send_telegram_msg(f"🎉 <b>Unpack Successful!</b>\nFolder: <code>UNPACK/{html.escape(pf.stem)}</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
                        except Exception as ex:
                            send_telegram_msg(f"❌ Unpack error on {html.escape(pf.name)}: {html.escape(str(ex))}", chat_id=chat_id)

            elif data == "btn_repack":
                unpack_dirs = [d for d in (data_path / "UNPACK").iterdir() if d.is_dir()]
                if not unpack_dirs:
                    send_telegram_msg("📦 <b>No unpacked folders found in UNPACK/!</b>\nPlease upload or unpack a PAK file first.", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
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

            elif data == "btn_compile":
                lua_files = [f for f in (data_path / "LUA").glob("*.*") if f.suffix.lower() in [".lua", ".txt"]]
                if not lua_files:
                    send_telegram_msg("📜 <b>No Lua files found in LUA/ folder.</b>\nPlease upload a <code>.lua</code> script first!", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
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

            elif data == "btn_setkey":
                user_key = get_user_key(user_id)
                status_txt = f"<code>{user_key[:8]}...{user_key[-4:]}</code>" if user_key else "<i>Not Set</i>"
                msg_txt = (
                    f"🔑 <b>API Key:</b> {status_txt}\n\n"
                    "Set Key: Send <code>/setkey YOUR_KEY</code>"
                )
                send_telegram_msg(msg_txt, chat_id=chat_id, reply_markup=get_main_keyboard_markup())

            elif data == "btn_clean":
                deleted = 0
                for d in [data_path / "INPUT", data_path / "OUTPUT", data_path / "UNPACK", data_path / "REPACK", data_path / "RESULT", data_path / "TEMP_INJECT"]:
                    if d.exists():
                        for f in d.iterdir():
                            try:
                                if f.is_file(): f.unlink()
                                elif f.is_dir(): shutil.rmtree(f, ignore_errors=True)
                                deleted += 1
                            except Exception: pass
                send_telegram_msg(f"🧹 Workspace Cleaned! Removed {deleted} items.", chat_id=chat_id, reply_markup=get_main_keyboard_markup())

            elif data == "btn_ai_help":
                send_telegram_msg("💡 Send: <code>/ai your question</code> or type directly!", chat_id=chat_id, reply_markup=get_main_keyboard_markup())

            elif data == "btn_restart":
                send_telegram_msg("🔄 Restarting Bot...", chat_id=chat_id)
                trigger_github_restart()
                sys.exit(0)
            return

        # 2. Handle Messages / Direct Files / Commands
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return
        
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            return

        from_user = msg.get("from", {})
        user_id = from_user.get("id", chat_id)

        text = (msg.get("text") or msg.get("caption") or "").strip()

        # Handle Uploaded Documents / Files
        if "document" in msg:
            doc = msg["document"]
            file_name = doc.get("file_name", "uploaded_file")
            file_id = doc.get("file_id")
            ext = Path(file_name).suffix.lower()

            send_telegram_msg(f"📥 <b>Received:</b> <code>{html.escape(file_name)}</code>\nProcessing...", chat_id=chat_id)

            if ext in [".pak", ".obb"]:
                save_path = data_path / "PAK" / file_name
                dl_ok, dl_err = download_telegram_file(file_id, save_path)
                if dl_ok:
                    send_telegram_msg(f"✅ Saved to <b>PAK/</b>. Unpacking...", chat_id=chat_id)
                    unpack_out = data_path / "UNPACK" / save_path.stem
                    try:
                        repack_pak_file_full(save_path, unpack_out, None)
                        send_telegram_msg(f"🎉 <b>Unpack Done!</b> Folder: <code>UNPACK/{html.escape(save_path.stem)}</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
                    except Exception as ex:
                        send_telegram_msg(f"❌ <b>Unpack Error:</b> {html.escape(str(ex))}", chat_id=chat_id)
                else:
                    send_telegram_msg(f"❌ <b>Download Failed:</b> {html.escape(dl_err)}", chat_id=chat_id)
            elif ext in [".lua", ".luac"]:
                save_path = data_path / "LUA" / file_name
                dl_ok, dl_err = download_telegram_file(file_id, save_path)
                if dl_ok:
                    send_telegram_msg(f"✅ Saved to <b>LUA/</b>. Compiling...", chat_id=chat_id)
                    try:
                        raw_code = save_path.read_text(encoding="utf-8", errors="ignore")
                        fixed = fix_lua_syntax_for_lua51(raw_code)
                        out_luac = data_path / "RESULT" / (save_path.stem + ".luac")
                        comp_ok, comp_msg = run_lua_compiler(save_path, out_luac)
                        if comp_ok and out_luac.exists():
                            send_telegram_document(out_luac, caption=f"✅ <b>Lua Compile Complete!</b>\n{out_luac.name}", chat_id=chat_id)
                        else:
                            send_telegram_msg(f"⚠️ <b>Compile Error:</b>\n<code>{html.escape(comp_msg[:500])}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ <b>Process Error:</b> {html.escape(str(ex))}", chat_id=chat_id)
                else:
                    send_telegram_msg(f"❌ <b>Download Failed:</b> {html.escape(dl_err)}", chat_id=chat_id)
            else:
                save_path = data_path / "INPUT" / file_name
                dl_ok, dl_err = download_telegram_file(file_id, save_path)
                if dl_ok:
                    send_telegram_msg(f"✅ Saved to <b>INPUT/</b>: <code>{html.escape(file_name)}</code>", chat_id=chat_id)
                else:
                    send_telegram_msg(f"❌ <b>Download Failed:</b> {html.escape(dl_err)}", chat_id=chat_id)
            return

        if not text:
            return

        # Clean command and handle group mentions
        first_word = text.split()[0].lower() if text else ""
        cmd_clean = first_word.split('@')[0] if '@' in first_word else first_word

        if cmd_clean in ["/start", "/help"]:
            welcome_msg = "⚡ <b>FEATURESTIC LEAKS BOT</b> ⚡\nChoose an option below:"
            send_telegram_msg(welcome_msg, chat_id=chat_id, reply_markup=get_main_keyboard_markup())

        elif cmd_clean == "/setkey" or cmd_clean == "/key":
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                send_telegram_msg("⚠️ Usage: <code>/setkey YOUR_API_KEY</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
            else:
                new_key = parts[1].strip()
                save_user_key(user_id, new_key)
                masked_key = f"{new_key[:8]}...{new_key[-4:]}"
                send_telegram_msg(f"✅ <b>Key Saved:</b> <code>{masked_key}</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())

        elif cmd_clean in ["/status", "/workspace"]:
            try:
                snapshot = get_live_workspace_context(data_path)
                send_telegram_msg(f"📊 <b>WORKSPACE LIVE SNAPSHOT:</b>\n<pre>{html.escape(snapshot)}</pre>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
            except Exception as e:
                send_telegram_msg(f"Error fetching status: {html.escape(str(e))}", chat_id=chat_id)

        elif cmd_clean == "/unpack":
            pak_files = [f for f in (data_path / "PAK").glob("*.*") if f.suffix.lower() in [".pak", ".obb"]]
            if not pak_files:
                send_telegram_msg("📦 No PAK/OBB files found in PAK/ folder.", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
            else:
                for pf in pak_files:
                    send_telegram_msg(f"⏳ Unpacking <code>{html.escape(pf.name)}</code>...", chat_id=chat_id)
                    unpack_out = data_path / "UNPACK" / pf.stem
                    try:
                        repack_pak_file_full(pf, unpack_out, None)
                        send_telegram_msg(f"🎉 <b>Unpack Successful!</b>\nFolder: <code>UNPACK/{html.escape(pf.stem)}</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
                    except Exception as ex:
                        send_telegram_msg(f"❌ Unpack error on {html.escape(pf.name)}: {html.escape(str(ex))}", chat_id=chat_id)

        elif cmd_clean == "/repack":
            unpack_dirs = [d for d in (data_path / "UNPACK").iterdir() if d.is_dir()]
            if not unpack_dirs:
                send_telegram_msg("📦 No unpacked folders found in UNPACK/!", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
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
                send_telegram_msg("📜 No Lua files found in LUA/ folder.", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
            else:
                for lf in lua_files:
                    send_telegram_msg(f"⏳ Compiling <code>{html.escape(lf.name)}</code>...", chat_id=chat_id)
                    try:
                        raw_code = lf.read_text(encoding="utf-8", errors="ignore")
                        fixed = fix_lua_syntax_for_lua51(raw_code)
                        out_luac = data_path / "RESULT" / (lf.stem + ".luac")
                        comp_ok, comp_msg = run_lua_compiler(lf, out_luac)
                        if comp_ok and out_luac.exists():
                            send_telegram_document(out_luac, caption=f"✅ <b>Lua Compile Complete!</b>\n{out_luac.name}", chat_id=chat_id)
                        else:
                            send_telegram_msg(f"⚠️ <b>Compile Error:</b>\n<code>{html.escape(comp_msg[:500])}</code>", chat_id=chat_id)
                    except Exception as ex:
                        send_telegram_msg(f"❌ Compile error on {html.escape(lf.name)}: {html.escape(str(ex))}", chat_id=chat_id)

        elif cmd_clean == "/ai":
            prompt = text[4:].strip() if len(text) > 3 else ""
            if not prompt:
                send_telegram_msg("💡 Usage: <code>/ai your question</code>", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
            else:
                send_telegram_msg("🤖 <i>OpenCode AI thinking...</i>", chat_id=chat_id)
                user_key = get_user_key(user_id)
                try:
                    ans = call_ai_api(prompt, override_key=user_key)
                    send_telegram_msg(f"🤖 <b>OpenCode AI Answer:</b>\n{html.escape(ans)}", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
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
            send_telegram_msg(f"🧹 Workspace Cleaned! Removed {deleted} items.", chat_id=chat_id, reply_markup=get_main_keyboard_markup())

        elif cmd_clean == "/restart":
            send_telegram_msg("🔄 Restarting Bot...", chat_id=chat_id)
            trigger_github_restart()
            sys.exit(0)

        else:
            send_telegram_msg("🤖 <i>OpenCode AI thinking...</i>", chat_id=chat_id)
            user_key = get_user_key(user_id)
            try:
                ans = call_ai_api(text, override_key=user_key)
                send_telegram_msg(f"🤖 <b>OpenCode AI Answer:</b>\n{html.escape(ans)}", chat_id=chat_id, reply_markup=get_main_keyboard_markup())
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
    send_telegram_msg(init_banner, reply_markup=get_main_keyboard_markup())
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
