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

    return None
