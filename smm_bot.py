import os
import json
import time
import tempfile
import requests
from typing import Dict, Any, Optional, List

from settings import (
    TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, DM_POLL_WINDOW_SECONDS,
    STATE_FILE, USERS_FILE, COOLDOWN_SECONDS, BOT_NAME
)
from agent import generate
from time_utils import now_wat, now_iso, ts
from http_utils import request_with_retry

# ===================== JSON HELPERS =====================

def _atomic_write(path: str, data: dict):
    fd, tmp = tempfile.mkstemp(dir=".", prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise

def _default_state() -> dict:
    return {
        "offset": 0,
        "last_request_at": {},
        "free_preview_used": [],
        "notified_admin": [],
        "known_names": {}
    }

def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return _default_state()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = _default_state()
        for k, v in base.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _default_state()

def save_state(data: dict):
    _atomic_write(STATE_FILE, data)

def _default_users() -> dict:
    return {
        "authorized": [],
        "pending": {},
        "alerts": {}
    }

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return _default_users()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        base = _default_users()
        for k, v in base.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _default_users()

def save_users(data: dict):
    _atomic_write(USERS_FILE, data)

# ===================== TELEGRAM HELPERS =====================

def tg_api(method: str, payload: dict = None) -> dict:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    resp = request_with_retry("POST", url, json=payload or {})
    return resp.json()

def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    chat_id = str(chat_id)
    # Hard Markdown safety: never send unpaired special chars
    safe_text = text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
    try:
        result = tg_api("sendMessage", {
            "chat_id": chat_id,
            "text": safe_text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        })
        return result.get("ok", False)
    except Exception as e:
        print(f"Send failed to {chat_id}: {e}")
        return False

def get_updates(offset: int) -> List[dict]:
    try:
        result = tg_api("getUpdates", {
            "offset": offset,
            "timeout": 20,
            "allowed_updates": ["message"]
        })
        return result.get("result", [])
    except Exception as e:
        print(f"getUpdates error: {e}")
        return []

# ===================== AUTHORIZATION =====================

def is_admin(chat_id: str) -> bool:
    return str(chat_id) == str(ADMIN_CHAT_ID)

def is_authorized(chat_id: str, users: dict) -> bool:
    return str(chat_id) in [str(x) for x in users.get("authorized", [])] or is_admin(chat_id)

def get_command_list() -> str:
    """Single source of truth for all command descriptions."""
    return (
        "• /plan — Full weekly content strategy + post ideas\n"
        "• /idea [platform] [niche] — High-engagement post idea + caption\n"
        "• /caption [topic] — Ready-to-post captions\n"
        "• /tip — Quick daily growth tip\n"
        "• /trend — Current social media trends\n"
        "• /help — Show this list again"
    )

# ===================== COMMAND HANDLERS =====================

def cmd_start(chat_id: str, text: str, state: dict, users: dict):
    name = state["known_names"].get(str(chat_id), "there")
    source = ""
    if text.startswith("/start ") and len(text.split()) > 1:
        source = text.split(maxsplit=1)[1][:40]

    if not is_authorized(chat_id, users):
        # Track pending inquiry
        users["pending"][str(chat_id)] = {
            "name": name,
            "source": source,
            "first_seen": now_iso()
        }
        save_users(users)

        if str(chat_id) not in state["notified_admin"] and ADMIN_CHAT_ID:
            send_message(ADMIN_CHAT_ID,
                f"New inquiry from {name} (chat ID {chat_id})\nSource: {source or 'none'}")
            state["notified_admin"].append(str(chat_id))
            save_state(state)

        # Free preview once
        if str(chat_id) not in state["free_preview_used"]:
            send_message(chat_id, "Here is a free quick tip while you explore:")
            tip = generate("Give one short, high-value social media growth tip.")
            send_message(chat_id, tip)
            state["free_preview_used"].append(str(chat_id))
            save_state(state)

        msg = (
            f"Welcome to {BOT_NAME}!\n\n"
            "I am your Expert Social Media Manager.\n\n"
            "Available commands:\n"
            f"{get_command_list()}\n\n"
            "This is currently free. Enjoy!"
        )
        send_message(chat_id, msg)
        return

    msg = (
        f"Welcome back, {name}!\n\n"
        f"Here's what I can do:\n"
        f"{get_command_list()}"
    )
    send_message(chat_id, msg)

def cmd_plan(chat_id: str):
    send_message(chat_id, "Generating your weekly SMM plan...")
    result = generate(
        "Create a complete weekly social media content strategy. "
        "Include themes, 5-7 strong post ideas with hooks, and sample captions. "
        "Make it practical and growth-focused."
    )
    send_message(chat_id, result)

def cmd_idea(chat_id: str, args: List[str]):
    query = " ".join(args) if args else "Instagram tech / growth audience"
    send_message(chat_id, "Crafting a strong post idea...")
    result = generate(
        f"Give one high-engagement post idea with a full ready-to-use caption for: {query}"
    )
    send_message(chat_id, result)

def cmd_caption(chat_id: str, args: List[str]):
    topic = " ".join(args) if args else "motivational content"
    send_message(chat_id, "Writing captions...")
    result = generate(
        f"Write 3 strong, ready-to-post captions for the topic: {topic}. "
        "Include emojis and a clear CTA where appropriate."
    )
    send_message(chat_id, result)

def cmd_tip(chat_id: str):
    result = generate("Give one short, actionable daily social media growth tip.")
    send_message(chat_id, result)

def cmd_trend(chat_id: str):
    result = generate(
        "What are the most relevant social media trends right now "
        "(Instagram, TikTok, LinkedIn, X)? Give practical ways a creator or brand can use them."
    )
    send_message(chat_id, result)

def cmd_help(chat_id: str):
    send_message(chat_id, f"Commands:\n\n{get_command_list()}")

# ===================== ADMIN =====================

def cmd_authorize(chat_id: str, args: List[str], users: dict, state: dict):
    if not is_admin(chat_id):
        return
    if not args:
        send_message(chat_id, "Send the chat ID you want to authorize.")
        return
    target = str(args[0])
    if target not in [str(x) for x in users["authorized"]]:
        users["authorized"].append(target)
        users["pending"].pop(target, None)
        save_users(users)
        send_message(chat_id, f"Authorized {target}")
        send_message(target, "You have been authorized. Enjoy full access!")
    else:
        send_message(chat_id, f"{target} is already authorized.")

def cmd_users(chat_id: str, users: dict, state: dict):
    if not is_admin(chat_id):
        return
    lines = []
    for uid in users.get("authorized", []):
        name = state["known_names"].get(str(uid), "Unknown")
        lines.append(f"{name} — {uid}")
    text = "Authorized users:\n" + ("\n".join(lines) if lines else "None yet")
    send_message(chat_id, text)

# ===================== MAIN LOOP =====================

def process_message(msg: dict, state: dict, users: dict):
    if "chat" not in msg or msg["chat"].get("type") != "private":
        return

    chat_id = str(msg["chat"]["id"])
    text = (msg.get("text") or "").strip()
    user = msg.get("from", {})
    name = user.get("first_name") or user.get("username") or "User"
    state["known_names"][chat_id] = name

    if not text.startswith("/"):
        return

    parts = text.split()
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]

    # Cooldown only for network commands
    network_cmds = {"/plan", "/idea", "/caption", "/tip", "/trend"}
    if cmd in network_cmds:
        last = state["last_request_at"].get(chat_id, 0)
        if ts() - last < COOLDOWN_SECONDS:
            send_message(chat_id, "Please wait a few seconds before the next request.")
            return
        state["last_request_at"][chat_id] = ts()

    if cmd in ("/start", "/help"):
        cmd_start(chat_id, text, state, users)
    elif cmd == "/plan":
        cmd_plan(chat_id)
    elif cmd == "/idea":
        cmd_idea(chat_id, args)
    elif cmd == "/caption":
        cmd_caption(chat_id, args)
    elif cmd == "/tip":
        cmd_tip(chat_id)
    elif cmd == "/trend":
        cmd_trend(chat_id)
    elif cmd == "/authorize":
        cmd_authorize(chat_id, args, users, state)
    elif cmd == "/users":
        cmd_users(chat_id, users, state)
    else:
        send_message(chat_id, "Unknown command. Use /help")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Missing TELEGRAM_BOT_TOKEN")
        return
    if not os.getenv("NVIDIA_API_KEY"):
        print("Missing NVIDIA_API_KEY")
        return

    print(f"{BOT_NAME} starting — listen window {DM_POLL_WINDOW_SECONDS}s")
    state = load_state()
    users = load_users()
    start = time.time()

    while time.time() - start < DM_POLL_WINDOW_SECONDS:
        updates = get_updates(state["offset"])
        for upd in updates:
            state["offset"] = upd["update_id"] + 1
            if "message" in upd:
                process_message(upd["message"], state, users)
        save_state(state)
        time.sleep(1.2)

    print("Listen window finished. Exiting cleanly.")

if __name__ == "__main__":
    main()
