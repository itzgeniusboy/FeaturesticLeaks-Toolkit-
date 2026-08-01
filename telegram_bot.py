#!/usr/bin/env python3
import os
import sys
import json
import logging
import asyncio
import base64
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("FeaturesticLeaksBot")

CONFIG_FILE = Path(__file__).resolve().parent / "telegram_bot_config.json"
USER_KEYS_FILE = Path(__file__).resolve().parent / "telegram_user_keys.json"

SYSTEM_PROMPT = """You are the official AI Assistant & Expert Guide for 'FeaturesticLeaks' — a powerful PAK/OBB & Lua Modding Tool for BGMI / PUBG Mobile / UE4 Android games.

Your primary mission is to TEACH users how to use the FeaturesticLeaks tool step-by-step. Whenever a user sends a screenshot of their screen or asks a question, explain clearly in simple Hindi / Hinglish (or English if requested) what option to select and how the tool works.

### FEATURESTIC LEAKS TOOL GUIDE & MENU MAP:

1. **PAK / OBB TOOLS MENU (Option [1] from Main Menu)**:
   - **Option [1] Unpack Package**: Extracts PAK or OBB files automatically to workspace (`UNPACK/` or `REPLACE/`). Supports Tencent Encrypted PAKs, OBBZSDIC, Mini_OBB, GamePatch files.
   - **Option [2] Repack & Inject**: Repacks modified files back into PAK format. Automatically matches original file size to prevent game crash / anti-cheat integrity checks!
   - **Option [3] One-Click Game Mods**: White Body / Item Nuller & Skin ID Swapper.
   - **Option [4] OBB Manager**: Unzip & Rezip OBB with size padding.
   - **Option [5] PAK Compare & Dump**: Compare 2 PAKs or dump index / offsets / hashes.
   - **Option [6] File Resizer & Equalizer**: Matches exact byte size of any file (PAK, OBB, LUA) using null bytes (`0x00`) or space bytes (`0x20`) against reference original files.

2. **LUA TOOLS MENU (Option [2] from Main Menu)**:
   - **Option [1] Decompiler**: Decompiles `.luac` / `.bytecode` into readable `.lua` source code. Automatically repairs obfuscated headers.
   - **Option [2] Compiler**: Compiles `.lua` back to `.luac` bytecode using `luac5.1` or `luajit`.
   - **Option [3] Script Merger & Studio**: Combines multiple Lua scripts or creates menu wrappers.
   - **Option [4] Optimizer & Syntax Checker**: Fixes Lua 5.1 syntax and checks block balance.
   - **Option [8] 1-Click Auto Lua Workflow**: Automatically fixes Lua 5.1 syntax errors (like standalone `local`, `continue`, `|`, `&`), compiles to `.luac`, and syncs output to all folders (`LUA/`, `RESULT/`, `REPLACE/`, `INJECT/`)!

3. **UTILITIES MENU (Option [3] from Main Menu)**:
   - **Option [1] UE4 String Tool**: Extract & repack `.uasset` / `.uexp` strings.
   - **Option [2] File Finder**: Search files by pattern.
   - **Option [5] File Resizer & Equalizer**: Match exact byte size of any file.

### RESPONSE STYLE:
- Friendly, clear, and direct teaching style in Hindi/Hinglish.
- Use clean formatting, bold option numbers, and step-by-step instructions.
"""

def load_user_keys() -> Dict[str, dict]:
    if USER_KEYS_FILE.exists():
        try:
            return json.loads(USER_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_all_keys(data: dict):
    USER_KEYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def get_user_keys_info(user_id: str) -> dict:
    data = load_user_keys()
    u_str = str(user_id)
    entry = data.get(u_str, {})
    if not isinstance(entry, dict):
        entry = {}

    provider = entry.get("provider", "gemini")
    gemini_keys = entry.get("gemini_keys", [])
    groq_keys = entry.get("groq_keys", [])

    if not gemini_keys and entry.get("provider") == "gemini" and entry.get("key"):
        gemini_keys = [entry["key"]]
    if not groq_keys and entry.get("provider") == "groq" and entry.get("key"):
        groq_keys = [entry["key"]]

    return {
        "provider": provider,
        "gemini_keys": list(gemini_keys),
        "groq_keys": list(groq_keys)
    }

def add_user_keys(user_id: str, provider: str, keys_list: List[str]) -> Tuple[int, int]:
    data = load_user_keys()
    u_str = str(user_id)
    info = get_user_keys_info(user_id)
    
    g_keys = info["gemini_keys"]
    q_keys = info["groq_keys"]

    added = 0
    target_list = g_keys if provider == "gemini" else q_keys

    for k in keys_list:
        clean_k = k.strip()
        if clean_k and clean_k not in target_list:
            target_list.append(clean_k)
            added += 1

    data[u_str] = {
        "provider": provider,
        "gemini_keys": g_keys,
        "groq_keys": q_keys
    }
    save_all_keys(data)
    return len(target_list), added

def update_user_keys_order(user_id: str, provider: str, keys_list: List[str]):
    data = load_user_keys()
    u_str = str(user_id)
    info = get_user_keys_info(user_id)
    if provider == "gemini":
        info["gemini_keys"] = keys_list
    else:
        info["groq_keys"] = keys_list
    info["provider"] = provider
    data[u_str] = info
    save_all_keys(data)

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_config(token: str):
    data = {"telegram_token": token}
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

async def analyze_with_gemini(api_key: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> Tuple[bool, str]:
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    parts = []
    if image_bytes:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question/Context:\n{prompt_text if prompt_text else 'Analyze this screenshot and explain step-by-step how to use FeaturesticLeaks tool to solve this issue or perform this action.'}"
    parts.append({"text": full_prompt})
    payload = {"contents": [{"parts": parts}]}
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30))
        if res.status_code == 200:
            data = res.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return True, text
            except (KeyError, IndexError):
                return False, "⚠️ Gemini response match nahi ho paya."
        else:
            return False, f"HTTP {res.status_code} - API Limit over ya Invalid Key"
    except Exception as e:
        return False, str(e)

async def analyze_with_groq(api_key: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> Tuple[bool, str]:
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama-3.2-11b-vision-preview" if image_bytes else "llama-3.3-70b-versatile"
    user_content = []
    if image_bytes:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
    user_content.append({"type": "text", "text": prompt_text if prompt_text else "Analyze screenshot and guide how to use FeaturesticLeaks tool."})
    payload = {"model": model, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}]}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers=headers, timeout=30))
        if res.status_code == 200:
            data = res.json()
            return True, data["choices"][0]["message"]["content"]
        else:
            return False, f"HTTP {res.status_code} - Model limit ya Invalid Key"
    except Exception as e:
        return False, str(e)

async def query_ai_for_user(user_id: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> str:
    info = get_user_keys_info(user_id)
    provider = info.get("provider", "gemini")
    gemini_keys = list(info.get("gemini_keys", []))
    groq_keys = list(info.get("groq_keys", []))

    if not gemini_keys and not groq_keys:
        return None

    primary_keys = gemini_keys if provider == "gemini" else groq_keys
    secondary_keys = groq_keys if provider == "gemini" else gemini_keys
    primary_prov = provider
    secondary_prov = "groq" if provider == "gemini" else "gemini"

    for idx, key in enumerate(primary_keys):
        if primary_prov == "gemini":
            ok, text = await analyze_with_gemini(key, prompt_text, image_bytes)
        else:
            ok, text = await analyze_with_groq(key, prompt_text, image_bytes)

        if ok:
            if idx > 0:
                primary_keys.insert(0, primary_keys.pop(idx))
                update_user_keys_order(user_id, primary_prov, primary_keys)
            return text
        else:
            logger.warning(f"{primary_prov.upper()} Key #{idx+1} failed: {text}. Rotating key...")

    if secondary_keys:
        for idx, key in enumerate(secondary_keys):
            if secondary_prov == "gemini":
                ok, text = await analyze_with_gemini(key, prompt_text, image_bytes)
            else:
                ok, text = await analyze_with_groq(key, prompt_text, image_bytes)

            if ok:
                if idx > 0:
                    secondary_keys.insert(0, secondary_keys.pop(idx))
                    update_user_keys_order(user_id, secondary_prov, secondary_keys)
                return text

    total = len(gemini_keys) + len(groq_keys)
    return f"❌ Aapki sabhi saved API keys ({total} keys) limit over ya invalid ho chuki hain! Kripya nayi Gemini ya Groq API key bhejien."

def run_bot():
    try:
        import telegram
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    except ImportError:
        print("❌ Missing python-telegram-bot! Run: pip install python-telegram-bot requests")
        return

    config = load_config()
    token = config.get("telegram_token") or os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ Telegram Bot Token is required!")
        return

    def get_main_keyboard():
        keyboard = [
            [
                InlineKeyboardButton("🚀 1-Click Auto Lua Fix & Compile", callback_data="btn_autolua_info"),
                InlineKeyboardButton("🌙 Decompile Bytecode", callback_data="btn_decompile_info")
            ],
            [
                InlineKeyboardButton("📦 Unpack PAK / OBB", callback_data="btn_unpack_info"),
                InlineKeyboardButton("📏 File Resizer & Equalizer", callback_data="btn_resizer_info")
            ],
            [
                InlineKeyboardButton("🔑 Add / View Saved Keys", callback_data="btn_setkey_info"),
                InlineKeyboardButton("❓ FeaturesticLeaks Tool Guide", callback_data="btn_guide_info")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    WELCOME_MESSAGE = (
        "👋 *Namaste! Welcome to Featurestic Leaks Interactive Modding Bot!* 🤖🔥\n\n"
        "Aap is bot se **FeaturesticLeaks PAK/OBB & Lua Modding Tool** ke sare kaam Telegram par hi direct kar sakte hain!\n\n"
        "✨ *MAIN FEATURES:* ✨\n"
        "• ⚡ *Auto Lua Fix & Compile:* Upload `.lua` file -> Auto-fixes syntax & >200 local limit -> Compiles to `.luac`!\n"
        "• 🌙 *Decompile Bytecode:* Upload `.luac` / `.bytecode` -> Instant `.lua` source code!\n"
        "• 📦 *Unpack PAK/OBB:* Upload `.pak` file -> Auto extracts files!\n"
        "• 🤖 *Multi-Key AI Assistant:* 1 se jada 10-50 API keys save karein! Auto key rotation & failover active!\n\n"
        "🔑 *AI Active karne ke liye apni free API Key bhejien (1 ya 10-50 ek sath paste karein):* 🔑\n"
        "• Google Gemini Key: [Get Free Key](https://aistudio.google.com/app/apikey)\n"
        "• Groq Key: [Get Free Key](https://console.groq.com/keys)"
    )

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        info = get_user_keys_info(u_id)
        g_cnt = len(info["gemini_keys"])
        q_cnt = len(info["groq_keys"])

        if g_cnt > 0 or q_cnt > 0:
            key_status = f"✅ *AI Active* (Gemini: *{g_cnt}* keys | Groq: *{q_cnt}* keys)\n_Auto Failover: Ek key khatam hogi to dusri automatic chalegi!_"
        else:
            key_status = "⚠️ *AI Key Not Set (Gemini ya Groq ki 1 ya multiple API keys chat me paste karein)*"

        text = f"{WELCOME_MESSAGE}\n\nStatus: {key_status}"
        await update.message.reply_text(text, reply_markup=get_main_keyboard(), parse_mode="Markdown", disable_web_page_preview=True)

    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "btn_autolua_info":
            await query.message.reply_text("🚀 *1-Click Auto Lua Fix & Compile:*\n\n👉 Upload `.lua` script file here.", parse_mode="Markdown")
        elif data == "btn_decompile_info":
            await query.message.reply_text("🌙 *Decompile Bytecode:*\n\n👉 Upload `.luac` bytecode file here.", parse_mode="Markdown")
        elif data == "btn_unpack_info":
            await query.message.reply_text("📦 *Unpack PAK / OBB:*\n\n👉 Use Option [1] PAK/OBB tools in FeaturesticLeaks.", parse_mode="Markdown")
        elif data == "btn_resizer_info":
            await query.message.reply_text("📏 *File Resizer & Size Equalizer:*\n\nMatch exact byte size of files.", parse_mode="Markdown")
        elif data == "btn_setkey_info":
            u_id = str(query.from_user.id)
            info = get_user_keys_info(u_id)
            g_cnt = len(info["gemini_keys"])
            q_cnt = len(info["groq_keys"])
            msg = (
                f"🔑 *API Keys Pool Status:*\n\n"
                f"• Gemini Keys Saved: *{g_cnt}*\n"
                f"• Groq Keys Saved: *{q_cnt}*\n\n"
                f"👉 Aap 1 se 50 tak kitni bhi API Keys chat me bhej sakte hain (1 per line ya ek sath copy-paste).\n"
                f"⚡ *Auto Rotation:* Ek key limit hit karne par bot automatically next key par switch kar lega!"
            )
            await query.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        elif data == "btn_guide_info":
            u_id = str(query.from_user.id)
            reply = await query_ai_for_user(u_id, "Explain all options of FeaturesticLeaks PAK/OBB & Lua tool in short clean Hindi guide.")
            if reply:
                await query.message.reply_text(reply, parse_mode="Markdown")
            else:
                await query.message.reply_text("⚠️ Kripya pehle Gemini ya Groq ki API key bhejien!", parse_mode="Markdown")

    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        doc = update.message.document
        filename = doc.file_name or "uploaded_file"
        file_ext = Path(filename).suffix.lower()
        status_msg = await update.message.reply_text(f"📥 *Receiving file '{filename}'...*", parse_mode="Markdown")
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            user_dir = Path(__file__).resolve().parent / "telegram_workspace" / u_id
            user_dir.mkdir(parents=True, exist_ok=True)
            local_path = user_dir / filename
            await tg_file.download_to_drive(local_path)

            if file_ext in [".lua", ".txt"]:
                await status_msg.edit_text(f"⚙️ *Processing '{filename}'... Auto-Fixing Syntax & Compiling to .luac...*", parse_mode="Markdown")
                sys.path.insert(0, str(Path(__file__).resolve().parent))
                try:
                    from FeaturesticLeaks import fix_lua_syntax_for_lua51
                    fixed_lua = fix_lua_syntax_for_lua51(local_path)
                except Exception:
                    fixed_lua = local_path

                out_luac = user_dir / f"{Path(filename).stem}_compiled.luac"
                all_compilers = ["luac5.1", "luac51", "luac", "luajit"]
                available = [c for c in all_compilers if shutil.which(c)]

                compiled_ok = False
                for compiler in available:
                    cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)] if compiler == "luajit" else [compiler, "-o", str(out_luac), str(fixed_lua)]
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode == 0:
                        compiled_ok = True
                        break

                if compiled_ok and out_luac.exists():
                    await status_msg.edit_text("✅ *Successfully Compiled! Sending .luac bytecode...*", parse_mode="Markdown")
                    await update.message.reply_document(document=open(out_luac, "rb"), filename=out_luac.name, caption="🎉 *Compiled .luac Bytecode Ready!*")
                else:
                    await status_msg.edit_text("✅ *Lua Syntax Fixed! Sending patched .lua script...*", parse_mode="Markdown")
                    await update.message.reply_document(document=open(fixed_lua, "rb"), filename=fixed_lua.name, caption="⚡ *Auto-Fixed .lua Script Ready!*")
            else:
                await status_msg.edit_text(f"📄 *File received: '{filename}'.*", parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error processing file: {str(e)}")

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        text = update.message.text.strip()

        gemini_found = re.findall(r'AIzaSy[A-Za-z0-9_\-]{33}', text)
        groq_found = re.findall(r'gsk_[A-Za-z0-9_\-]+', text)

        if gemini_found:
            total, added = add_user_keys(u_id, "gemini", gemini_found)
            msg = f"✅ *Saved {added} New Gemini API Key(s)!* 🎉\n\n• Active Gemini Pool: *{total} Keys*\n• Auto Key Failover: *ACTIVE*\n\n_Aap aur keys bhi bhej sakte hain (10-50 keys support)_"
            await update.message.reply_text(msg, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            return

        if groq_found:
            total, added = add_user_keys(u_id, "groq", groq_found)
            msg = f"✅ *Saved {added} New Groq API Key(s)!* 🎉\n\n• Active Groq Pool: *{total} Keys*\n• Auto Key Failover: *ACTIVE*\n\n_Aap aur keys bhi bhej sakte hain (10-50 keys support)_"
            await update.message.reply_text(msg, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            return

        if "aistudio" in text.lower() or "gemini" in text.lower():
            raw = re.sub(r'[^a-zA-Z0-9_\-]', '', text)
            if len(raw) >= 30:
                total, added = add_user_keys(u_id, "gemini", [raw])
                await update.message.reply_text(f"✅ *Gemini Key Saved! Total Keys: {total}*", reply_markup=get_main_keyboard(), parse_mode="Markdown")
                return

        if "groq" in text.lower():
            raw = re.sub(r'[^a-zA-Z0-9_\-]', '', text)
            if len(raw) >= 30:
                total, added = add_user_keys(u_id, "groq", [raw])
                await update.message.reply_text(f"✅ *Groq Key Saved! Total Keys: {total}*", reply_markup=get_main_keyboard(), parse_mode="Markdown")
                return

        if text.lower() in ["hi", "hello", "hy", "hey", "help", "start", "/start", "menu"]:
            await start_cmd(update, context)
            return

        info = get_user_keys_info(u_id)
        if not info["gemini_keys"] and not info["groq_keys"]:
            await update.message.reply_text("⚠️ *API Key is required to ask AI! (Send Gemini or Groq API key(s))*", reply_markup=get_main_keyboard(), parse_mode="Markdown", disable_web_page_preview=True)
            return

        msg = await update.message.reply_text("🤖 *Analyzing tool question...*", parse_mode="Markdown")
        reply = await query_ai_for_user(u_id, text)
        await msg.edit_text(reply, reply_markup=get_main_keyboard(), parse_mode="Markdown")

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        info = get_user_keys_info(u_id)
        if not info["gemini_keys"] and not info["groq_keys"]:
            await update.message.reply_text("⚠️ *API Key is required to analyze screenshots!*", reply_markup=get_main_keyboard(), parse_mode="Markdown", disable_web_page_preview=True)
            return

        msg = await update.message.reply_text("🔍 *Analyzing screenshot...*", parse_mode="Markdown")
        try:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            img_bytes = await file.download_as_bytearray()
            caption = update.message.caption or ""
            reply = await query_ai_for_user(u_id, caption, bytes(img_bytes))
            await msg.edit_text(reply, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ Error analyzing screenshot: {str(e)}")

    logger.info("🚀 Telegram AI Vision Bot running in background...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.run_polling()

if __name__ == "__main__":
    run_bot()
