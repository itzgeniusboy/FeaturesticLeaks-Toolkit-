#!/usr/bin/env python3
"""
===============================================================================
🤖 FEATURESTIC LEAKS — TELEGRAM AI VISION BOT ASSISTANT 🤖
===============================================================================
This bot connects Telegram with Google Gemini AI (Gemini Flash Vision).
Users can send screenshots, error photos, or text questions on Telegram.
The bot analyzes the image and explains step-by-step how to solve the issue
or use the FeaturesticLeaks PAK/OBB/Lua modding tool!
===============================================================================
"""

import os
import sys
import json
import logging
import asyncio
import base64
import re
from pathlib import Path
from typing import Optional, Dict

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FeaturesticLeaksBot")

CONFIG_FILE = Path(__file__).parent / "telegram_bot_config.json"
USER_KEYS_FILE = Path(__file__).parent / "telegram_user_keys.json"

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

### COMMON USER QUESTIONS & SOLUTION GUIDE:
- *Q: "Decompile karne ke baad Lua file ka size bada ho gaya, kya karein?"*
  -> Solution: Edit `.lua` file, then use **LUA Tools -> Option [8] 1-Click Auto Lua Workflow**. It will auto-fix syntax errors and compile it back to small `.luac` bytecode!
- *Q: "Repack karne ke baad game crash ho raha hai"*
  -> Solution: Use **File Resizer & Equalizer** (PAK Menu Option [6]) to match the exact byte size of the original PAK file!

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

def save_user_key(user_id: str, provider: str, key: str):
    keys = load_user_keys()
    keys[str(user_id)] = {"provider": provider, "key": key}
    USER_KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")

def get_user_key(user_id: str) -> Optional[dict]:
    keys = load_user_keys()
    return keys.get(str(user_id))

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

async def analyze_with_gemini(api_key: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> str:
    import requests
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    parts = []
    if image_bytes:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64_img
            }
        })
    
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question/Context:\n{prompt_text if prompt_text else 'Analyze this screenshot and explain step-by-step how to use FeaturesticLeaks tool to solve this issue or perform this action.'}"
    parts.append({"text": full_prompt})
    
    payload = {"contents": [{"parts": parts}]}

    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        )
        if res.status_code == 200:
            data = res.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return "⚠️ AI response match nahi ho paya. Kripya punah try karein."
        else:
            return f"❌ Gemini API Error ({res.status_code}): Invalid Key ya API Limit over."
    except Exception as e:
        return f"❌ AI Connection Error: {str(e)}"

async def analyze_with_groq(api_key: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> str:
    import requests
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    model = "llama-3.2-11b-vision-preview" if image_bytes else "llama-3.3-70b-versatile"
    
    user_content = []
    if image_bytes:
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
        })
    
    user_content.append({
        "type": "text",
        "text": prompt_text if prompt_text else "Analyze screenshot and guide how to use FeaturesticLeaks tool."
    })

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, json=payload, headers=headers, timeout=30)
        )
        if res.status_code == 200:
            data = res.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"❌ Groq API Error ({res.status_code}): Invalid Key ya Model Limit."
    except Exception as e:
        return f"❌ AI Connection Error: {str(e)}"

async def query_ai_for_user(user_id: str, prompt_text: str, image_bytes: Optional[bytes] = None) -> str:
    user_info = get_user_key(user_id)
    if not user_info:
        return None
    
    provider = user_info.get("provider")
    key = user_info.get("key")
    
    if provider == "groq":
        return await analyze_with_groq(key, prompt_text, image_bytes)
    else:
        return await analyze_with_gemini(key, prompt_text, image_bytes)

def run_bot():
    try:
        import telegram
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
    except ImportError:
        print("❌ Missing python-telegram-bot! Run: pip install python-telegram-bot requests")
        return

    config = load_config()
    token = config.get("telegram_token") or os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        print("=========================================================")
        print("🤖 FEATURESTIC LEAKS TELEGRAM AI BOT SETUP 🤖")
        print("=========================================================")
        token = input("-> Enter Telegram Bot Token (from @BotFather): ").strip()
        if token:
            save_config(token)
            print("✅ Configuration saved to telegram_bot_config.json")
        else:
            print("❌ Telegram Bot Token is required!")
            return

    WELCOME_MESSAGE = (
        "👋 *Namaste! Welcome to Featurestic Leaks AI Guide Bot!* 🤖\n\n"
        "Main aapko **FeaturesticLeaks PAK/OBB & Lua Modding Tool** chalana sikhaunga!\n\n"
        "⚡ *AI feature active karne ke liye apni free API Key bhejien:* ⚡\n\n"
        "🔑 *1. Google Gemini API Key (Free):*\n"
        "🔗 [Get Gemini API Key Here](https://aistudio.google.com/app/apikey)\n\n"
        "🔑 *2. Groq API Key (Free):*\n"
        "🔗 [Get Groq API Key Here](https://console.groq.com/keys)\n\n"
        "👉 Upar diye gaye kisi ek link se API Key copy karke yahan chat me paste kar dein!\n"
        "Bot aapki API key ko save kar lega aur aapko har tool option ka complete guide dega! 🔥"
    )

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        user_info = get_user_key(u_id)
        if user_info:
            await update.message.reply_text(
                f"✅ *Aapki API Key ({user_info['provider'].upper()}) already active hai!* 🔥\n\n"
                "Aap kisi bhi screen ka **Screenshot** bhejien ya question poochhein, main aapko **FeaturesticLeaks Tool** chalana sikha dunga!",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown", disable_web_page_preview=True)

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        text = update.message.text.strip()

        # Check if user sent an API key
        if text.startswith("AIzaSy") or "aistudio" in text.lower():
            # Clean gemini key
            key = re.sub(r'[^a-zA-Z0-9_\-]', '', text)
            save_user_key(u_id, "gemini", key)
            await update.message.reply_text(
                "✅ *Google Gemini API Key Saved Successfully!* 🎉\n\n"
                "Ab aap mujhe Tool ka koi bhi **Screenshot** bhejien ya koi question poochhein, main aapko step-by-step guidance dunga!",
                parse_mode="Markdown"
            )
            return

        if text.startswith("gsk_") or "groq" in text.lower():
            key = re.sub(r'[^a-zA-Z0-9_\-]', '', text)
            save_user_key(u_id, "groq", key)
            await update.message.reply_text(
                "✅ *Groq API Key Saved Successfully!* 🎉\n\n"
                "Ab aap mujhe Tool ka koi bhi **Screenshot** bhejien ya koi question poochhein, main aapko step-by-step guidance dunga!",
                parse_mode="Markdown"
            )
            return

        # Check if greeting
        if text.lower() in ["hi", "hello", "hy", "hey", "help", "start", "/start"]:
            await start_cmd(update, context)
            return

        # User key check
        user_info = get_user_key(u_id)
        if not user_info:
            await update.message.reply_text(
                "⚠️ *API Key is required to ask AI!*\n\n"
                "Kripya apni **Gemini** ya **Groq** API key chat me send karein:\n\n"
                "🔗 [Get Gemini API Key](https://aistudio.google.com/app/apikey)\n"
                "🔗 [Get Groq API Key](https://console.groq.com/keys)",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return

        msg = await update.message.reply_text("🤖 *Analyzing tool question...*", parse_mode="Markdown")
        reply = await query_ai_for_user(u_id, text)
        await msg.edit_text(reply, parse_mode="Markdown")

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        u_id = str(update.effective_user.id)
        user_info = get_user_key(u_id)

        if not user_info:
            await update.message.reply_text(
                "⚠️ *API Key is required to analyze screenshots!*\n\n"
                "Kripya pehle apni **Gemini** ya **Groq** API key chat me paste karein:\n\n"
                "🔗 [Get Gemini API Key](https://aistudio.google.com/app/apikey)\n"
                "🔗 [Get Groq API Key](https://console.groq.com/keys)",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            return

        msg = await update.message.reply_text("🔍 *Analyzing screenshot to guide you on FeaturesticLeaks tool...*", parse_mode="Markdown")
        try:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            img_bytes = await file.download_as_bytearray()
            
            caption = update.message.caption or ""
            reply = await query_ai_for_user(u_id, caption, bytes(img_bytes))
            await msg.edit_text(reply, parse_mode="Markdown")
        except Exception as e:
            await msg.edit_text(f"❌ Error analyzing screenshot: {str(e)}")

    print("\n🚀 Starting Telegram Bot... Press Ctrl+C to stop.")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    app.run_polling()

if __name__ == "__main__":
    run_bot()

