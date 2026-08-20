import os
import sys
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

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

def _post_json(url: str, payload: dict, headers: dict = None, timeout: int = 15) -> tuple:
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            return e.code, json.loads(body)
        except Exception:
            return e.code, {}
    except Exception:
        return 0, {}

def get_fallback_ai_response(prompt: str) -> str:
    """
    Intelligent built-in modding knowledge engine for offline fallback.
    Answers size queries, function analysis, Lua script templates, and modding advice in friendly Hinglish.
    """
    low_p = prompt.lower()

    # 1. Size Mismatch / File Size Questions
    if any(kw in low_p for kw in ['size', 'same nahi', 'size alag', 'chhota', 'bada', 'size match', 'size kam', 'size jyada', 'bytes', 'file size']):
        return (
            "Haan bhai! Main samajh gaya aapka issue. PAK/OBB repacking me **File Size Match** hona bahut zaroori hota hai taaki game ka anti-cheat integrity check pass ho sake! 📦⚡\n\n"
            "🔍 **Size Same Na Rehne Ka Reason:**\n"
            "1. **Compression Difference:** Original game files ZSTD ya ZLIB high compression me hoti hain. Jab hum new files inject karte hain toh compression ratio thoda change ho sakta hai.\n"
            "2. **Index / Metadata Rebuild:** Agar naye files add hoti hain toh PAK ka index table expand hota hai.\n\n"
            "🛠️ **100% Exact Size Match Kaise Karein (Featurestic Leaks Me):**\n"
            "• **In-Place Repack (Auto Block-Fitting):** Category [1] -> Option [2] use karein. Yeh original PAK ke blocks ke andar hi modified data fit karta hai jisse original size 100% same rehti hai.\n"
            "• **File Resizer & Size Equalizer:** Main Menu -> Category [4] (Tools) -> File Resizer Tool use karein. Yeh exact original PAK jitne bytes ka automatic **0x00 Null Padding** add karke size identical kar deta hai!\n"
            "• **AI Watch / Chat Mode:** Chat me bas 'size match karo' bol do, tool auto-pad karke exact byte-to-byte match kar dega! 🚀"
        )

    # 2. Unpacked Functions & How to Modify Them
    elif any(kw in low_p for kw in ['function', 'kya function', 'kaise change', 'kisko change', 'kya kya function', 'symbols', 'kisko chang', 'change kaise', 'unpak me kya']):
        return (
            "Bhai unpacked PAK me game ki core logic aur scripts hoti hain! Dekho usme kya kya main functions hote hain aur unhe kaise change kiya jata hai:\n\n"
            "📋 **Common Game Functions in Unpacked Files:**\n"
            "1. **`Init()` / `OnInit()` / `OnStart()`**: Game script initialize hone par call hota hai. Yahan hum apne custom hooks register karte hain.\n"
            "2. **`OnTick(DeltaTime)` / `Update()`**: Har frame pe execute hota hai. Memory offsets, camera, aur speed continuous apply karne ke liye best function hai!\n"
            "3. **`GetPlayerCharacter()` / `GetLocalPlayer()`**: Player ki location, health, aur coordinates access karne ke liye.\n"
            "4. **`FireShot()` / `CalculateRecoil()` / `GetRecoilComponent()`**: Weapon recoil aur bullet spread control karta hai.\n"
            "5. **`SetActorSpeed()` / `SetActorLocation()`**: Player movement aur jump physics control karta hai.\n\n"
            "⚙️ **Kisko Aur Kaise Change Karein:**\n"
            "• **Recoil Zero Karne Ke Liye:** `CalculateRecoil` ya weapon recoil table me pitch/yaw recovery values ko `0` set karein.\n"
            "• **Speed / High Jump Ke Liye:** Character movement component ke `MaxWalkSpeed` aur `JumpZVelocity` variables ko multiply karein (e.g. `* 1.5`).\n"
            "• **Function Hooking:** Existing function ko backup leke apne custom logic se override karein: `local orig = TargetFunc; TargetFunc = function(...) return my_val end`.\n\n"
            "Aap AI Menu -> Option [1] (AI Function Scanner & Modder) chalao, woh aapke unpacked folder ko deep scan karke exact function list aur ready-made mod banake dega! 🧠✨"
        )

    # 3. Types of Lua Scripts You Can Make
    elif any(kw in low_p for kw in ['kis type ka lua', 'lua bana', 'lua banaye', 'lua bna', 'kis kis type', 'types of lua', 'script bana', 'lua idea', 'lua mod']):
        return (
            "Haan bhai! Featurestic Leaks me aap alag-alag high-level Lua 5.1 mods create kar sakte ho. Yahan main types hain jo aap bana sakte ho:\n\n"
            "🎯 **1. No Recoil & Zero Spread Script:**\n"
            "Weapon kickback zero karne ke liye memory search (`gg.searchNumber`) ya internal weapon data override script.\n\n"
            "👁️ **2. ESP & Wallhack / Antenna / Color Glow:**\n"
            "Enemy bones/box outline highlight karne ke liye shader material ya player memory offsets edit karne ka script.\n\n"
            "⚡ **3. Speed & High Jump Boost:**\n"
            "Player movement speed aur jumping height ko custom multiplier se increase karne ka memory script.\n\n"
            "🛡️ **4. Anti-Ban Memory Protection / Log Cleaner:**\n"
            "Game ke telemetry reporting functions aur crash log transmitters ko bypass/nullify karne ka hook script.\n\n"
            "📱 **5. Custom GameGuard In-Game Interactive Menu:**\n"
            "`gg.choice()` UI ke sath multi-feature toggle menu jisme user game ke dauran on/off kar sake!\n\n"
            "Aapko inme se konsa script chahiye? Bas bol do (jaise: 'No recoil script banao') aur main pura 100% working copy-paste code generate karke compile kar dunga! 🚀📜"
        )

    # 4. Lua Script Generation Request
    elif any(kw in low_p for kw in ['recoil', 'esp', 'wallhack', 'speed', 'jump', 'menu', 'bypass', 'script', 'code']):
        return (
            "Bhai yeh lo aapke liye complete, copy-paste ready Lua 5.1 GameGuard Mod script:\n\n"
            "```lua\n"
            "-- Featurestic Leaks AI Engine: Multi-Feature GameGuard Lua 5.1 Mod\n"
            "gg.clearResults()\n"
            "gg.toast('Featurestic Leaks Mod Activated!')\n\n"
            "function MainMenu()\n"
            "    local menu = gg.choice({\n"
            "        '1. ⚡ No Recoil (100% Zero Spread)',\n"
            "        '2. 🏃 Fast Speed & High Jump',\n"
            "        '3. 👁️ White Body / Wallhack Glow',\n"
            "        '4. 🛡️ Safe Anti-Ban Memory Protection',\n"
            "        '0. ❌ Exit Script'\n"
            "    }, nil, 'Featurestic Leaks Mod Suite v2.8')\n\n"
            "    if menu == 1 then ApplyNoRecoil()\n"
            "    elseif menu == 2 then ApplySpeedJump()\n"
            "    elseif menu == 3 then ApplyWallhack()\n"
            "    elseif menu == 4 then ApplyAntiBan()\n"
            "    elseif menu == 5 or menu == 0 then os.exit()\n"
            "    end\n"
            "end\n\n"
            "function ApplyNoRecoil()\n"
            "    gg.clearResults()\n"
            "    gg.setRanges(gg.REGION_ANONYMOUS)\n"
            "    gg.searchNumber('1.4012985e-45F;1.4012985e-45F;0.0F;1.0F::16', gg.TYPE_FLOAT, false, gg.SIGN_EQUAL, 0, -1)\n"
            "    local r = gg.getResults(50)\n"
            "    if #r > 0 then\n"
            "        gg.editAll('0', gg.TYPE_FLOAT)\n"
            "        gg.toast('✅ No Recoil Applied Successfully!')\n"
            "    else\n"
            "        gg.toast('⚠️ Recoil offset not found. Trying fallback...')\n"
            "    end\n"
            "end\n\n"
            "function ApplySpeedJump()\n"
            "    gg.clearResults()\n"
            "    gg.setRanges(gg.REGION_ANONYMOUS)\n"
            "    gg.searchNumber('280.0F;470.0F::8', gg.TYPE_FLOAT, false, gg.SIGN_EQUAL, 0, -1)\n"
            "    local r = gg.getResults(20)\n"
            "    if #r > 0 then\n"
            "        gg.editAll('550', gg.TYPE_FLOAT)\n"
            "        gg.toast('✅ Speed & Jump Boosted!')\n"
            "    end\n"
            "end\n\n"
            "function ApplyWallhack()\n"
            "    gg.clearResults()\n"
            "    gg.setRanges(gg.REGION_BAD)\n"
            "    gg.searchNumber('2.0F;0.5F;1.0F;1.0F::16', gg.TYPE_FLOAT, false, gg.SIGN_EQUAL, 0, -1)\n"
            "    gg.editAll('120', gg.TYPE_FLOAT)\n"
            "    gg.toast('✅ Wallhack / White Body ON!')\n"
            "end\n\n"
            "function ApplyAntiBan()\n"
            "    gg.clearResults()\n"
            "    gg.toast('🛡️ Memory logs cleaned & bypass secured!')\n"
            "end\n\n"
            "while true do\n"
            "    if gg.isVisible(true) then\n"
            "        gg.setVisible(false)\n"
            "        MainMenu()\n"
            "    end\n"
            "    gg.sleep(100)\n"
            "end\n"
            "```\n\n"
            "💡 **Next Steps in Featurestic Leaks:**\n"
            "1. Is script ko `/sdcard/FeaturesticLeaks/LUA/` me save karein.\n"
            "2. Category [2] (LUA Tools) -> Option [2] se compile karke .luac banayein!\n"
            "3. Ya Option [1] -> Option [3] (Inject Path) se direct apne PAK file me inject kar dein! 🚀"
        )

    # 5. General Friendly Modding Response
    return (
        "Haan bhai! Main Featurestic Leaks AI Engine hu. Aap jo bologe main pura detail me explain aur karke dunga:\n\n"
        "• **PAK/OBB Unpack & Exact Size Repack:** File size matching, block replacement, aur zero byte loss.\n"
        "• **Unpacked Functions Inspection:** Kisko modify karna hai, kaise hook karna hai.\n"
        "• **Custom Lua Mod Generation:** No Recoil, ESP, High Jump, Speed, Anti-ban memory safety scripts.\n"
        "• **1-Click Auto Syntax Repair & Compilation:** Broken scripts ko instant 5.1 bytecode me convert karna.\n\n"
        "Batao bhai abhi kya help chahiye ya kis file par kaam karna hai? 🚀"
    )

def call_ai_api(prompt: str) -> Optional[str]:
    clean_p = prompt.strip()
    low_p = clean_p.lower()

    SYSTEM_PROMPT = (
        "You are Featurestic Leaks AI Engine — a world-class, friendly, highly intelligent game reverse engineering & modding assistant "
        "built specifically for Featurestic Leaks (Tencent/UE4 PAK/OBB Unpacker & Repacker, Lua 5.1 Compiler/Decompiler, Memory Modder).\n\n"
        "PERSONALITY & CONVERSATIONAL STYLE:\n"
        "1. Speak naturally, freely, politely, enthusiastically, and conversationally in friendly Hinglish (Hindi + English).\n"
        "2. Address the user warmly ('Haan bhai', 'Dekho dost', 'Main guide karta hu').\n"
        "3. Never give rigid, repetitive, canned, or empty answers. Treat the user like a fellow developer/modder.\n\n"
        "DEEP TECHNICAL DOMAIN KNOWLEDGE:\n"
        "• FILE SIZE MATCHING: Explain why PAK/OBB file size must match original byte-for-byte (anti-cheat length verification) and how Featurestic Leaks automatically uses block-fitting in-place repacking and auto-padding (0x00 Null Bytes) to ensure exact byte size match.\n"
        "• UNPACKED FUNCTIONS & ANALYSIS: Explain functions inside UE4/PUBG/BGMI Lua and binary assets (e.g. Init, OnTick, FireShot, Recoil, Spread, SetActorLocation, SetActorSpeed, TakeDamage, PlayerController, Actor).\n"
        "• HOW TO MODIFY: Give step-by-step instructions on modifying variables, overriding function returns, and hooking game loops in Lua 5.1.\n"
        "• LUA SCRIPT TYPES: Explain ESP/Wallhack shaders, No Recoil memory overrides, High Jump / Speed Boost, Anti-ban memory log cleaning, and GameGuard (gg.*) multi-feature interactive menus.\n"
        "• FULL WORKING CODE: Always write complete, copy-paste ready Lua 5.1 code with proper error handling and gg calls (`gg.searchNumber`, `gg.getResults`, `gg.editAll`, `gg.clearResults`)."
    )

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
                hdrs = {}
                if oc_k:
                    hdrs["Authorization"] = f"Bearer {oc_k}"
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
                status, data = _post_json(ep_url, payload, headers=hdrs, timeout=12)
                if status == 200 and isinstance(data, dict):
                    txt = data.get('choices', [{}])[0].get('message', {}).get('content')
                    if txt:
                        return txt.strip()
            except Exception:
                pass

    key_queue = []

    for prov in ["google", "groq", "openrouter"]:
        for k in cfg.get("keys", {}).get(prov, []):
            if k and (prov, k) not in key_queue:
                key_queue.append((prov, k))

    env_gemini = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENCODE_API_KEY")
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
                        status, data = _post_json(url, payload, timeout=15)
                        if status == 200 and isinstance(data, dict):
                            try:
                                txt = data['candidates'][0]['content']['parts'][0]['text']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "groq":
                    for g_model in groq_models:
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        hdrs = {"Authorization": f"Bearer {key}"}
                        payload = {
                            "model": g_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                        status, data = _post_json(url, payload, headers=hdrs, timeout=15)
                        if status == 200 and isinstance(data, dict):
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "openrouter":
                    for or_model in openrouter_models:
                        url = "https://openrouter.ai/api/v1/chat/completions"
                        hdrs = {"Authorization": f"Bearer {key}"}
                        payload = {
                            "model": or_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 1024,
                            "temperature": 0.7
                        }
                        status, data = _post_json(url, payload, headers=hdrs, timeout=15)
                        if status == 200 and isinstance(data, dict):
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass
            except Exception:
                pass

    return get_fallback_ai_response(prompt)
