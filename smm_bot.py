import os
import json
import time
import tempfile
from typing import List

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
        "known_names": {},
        "profiles": {}
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

def send_message(chat_id: str, text: str) -> bool:
    """Plain text only — no Markdown, no asterisks."""
    chat_id = str(chat_id)
    try:
        result = tg_api("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        })
        return result.get("ok", False)
    except Exception as e:
        print(f"Send failed to {chat_id}: {e}")
        return False

def get_updates(offset: int) -> list:
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

# ===================== PROFILE & CONVERSATION =====================

def get_profile(chat_id: str, state: dict) -> dict:
    return state["profiles"].get(str(chat_id), {})

def update_profile(chat_id: str, state: dict, **kwargs):
    cid = str(chat_id)
    if cid not in state["profiles"]:
        state["profiles"][cid] = {}
    state["profiles"][cid].update(kwargs)
    save_state(state)

def profile_summary(profile: dict) -> str:
    if not profile:
        return "No brand information collected yet."
    parts = []
    if profile.get("brand_name"):
        parts.append(f"Brand: {profile['brand_name']}")
    if profile.get("niche"):
        parts.append(f"Niche: {profile['niche']}")
    if profile.get("goal"):
        parts.append(f"Main goal: {profile['goal']}")
    if profile.get("challenge"):
        parts.append(f"Biggest challenge: {profile['challenge']}")
    if profile.get("personality"):
        parts.append(f"Personality / Tone: {profile['personality']}")
    return "\n".join(parts) if parts else "Profile started but incomplete."

def build_context(chat_id: str, state: dict) -> str:
    profile = get_profile(chat_id, state)
    if not profile:
        return "No brand profile available yet."
    return (
        f"Brand name: {profile.get('brand_name', 'Not set')}\n"
        f"Niche: {profile.get('niche', 'Not set')}\n"
        f"Main goal: {profile.get('goal', 'Not set')}\n"
        f"Biggest challenge: {profile.get('challenge', 'Not set')}\n"
        f"Personality / Tone: {profile.get('personality', 'Not set')}"
    )

def is_admin(chat_id: str) -> bool:
    return str(chat_id) == str(ADMIN_CHAT_ID)

def is_authorized(chat_id: str, users: dict) -> bool:
    return str(chat_id) in [str(x) for x in users.get("authorized", [])] or is_admin(chat_id)

def get_command_list() -> str:
    return (
        "Here is what I can help you with:\n\n"
        "/setup — Tell me about your brand (recommended first)\n"
        "/plan — Personalized weekly strategy\n"
        "/idea — Post idea based on your brand\n"
        "/hooks — Strong hooks for your niche\n"
        "/caption — Captions written for you\n"
        "/calendar — 7-day content calendar\n"
        "/series — Content series ideas\n"
        "/tip — Sharp growth tip\n"
        "/trend — Current useful trends\n"
        "/audit — Honest strategy audit\n"
        "/profile — Show what I know about your brand\n"
        "/reset — Clear your brand profile and start over\n"
        "/help — Show this list"
    )

# ===================== COMMAND HANDLERS =====================

def cmd_start(chat_id: str, text: str, state: dict, users: dict):
    name = state["known_names"].get(str(chat_id), "there")
    profile = get_profile(chat_id, state)

    if not profile.get("brand_name"):
        send_message(chat_id,
            f"Hey {name}. I'm your senior Social Media Manager.\n\n"
            "I just need 5 quick answers so I can give you personalized advice instead of generic content.\n\n"
            "1/5 — What is your brand or project name?\n"
            "Example: GlowSkin, FitWithAda, TechLaunch, etc."
        )
        update_profile(chat_id, state, stage="awaiting_brand_name")
        return

    send_message(chat_id,
        f"Welcome back, {name}.\n\n"
        f"Here's what I know about your brand:\n{profile_summary(profile)}\n\n"
        f"{get_command_list()}"
    )

def cmd_setup(chat_id: str, state: dict):
    send_message(chat_id,
        "Let's quickly set up your brand profile (only 5 questions).\n\n"
        "1/5 — What is your brand or project name?\n"
        "Example: GlowSkin, FitWithAda, TechLaunch, etc."
    )
    update_profile(chat_id, state, stage="awaiting_brand_name")

def cmd_reset(chat_id: str, state: dict):
    cid = str(chat_id)
    if cid in state.get("profiles", {}):
        del state["profiles"][cid]
        save_state(state)

    send_message(chat_id,
        "Your brand profile has been reset.\n\n"
        "Let's start fresh.\n\n"
        "1/5 — What is your brand or project name?\n"
        "Example: GlowSkin, FitWithAda, TechLaunch, etc."
    )
    update_profile(chat_id, state, stage="awaiting_brand_name")

def handle_conversation(chat_id: str, text: str, state: dict):
    """Exactly 5 questions. /back only available from question 2 onwards."""
    profile = get_profile(chat_id, state)
    stage = profile.get("stage")
    text_clean = text.strip().lower()

    # Handle /back (only works from question 2+)
    if text_clean == "/back":
        if stage == "awaiting_niche":
            update_profile(chat_id, state, stage="awaiting_brand_name")
            send_message(chat_id,
                "Okay, going back.\n\n"
                "1/5 — What is your brand or project name?\n"
                "Example: GlowSkin, FitWithAda, TechLaunch, etc."
            )
            return True

        if stage == "awaiting_goal":
            update_profile(chat_id, state, stage="awaiting_niche")
            send_message(chat_id,
                "Okay, going back.\n\n"
                "2/5 — What niche or industry are you in?\n"
                "Example: Skincare, Fitness coaching, Personal branding, Real estate, Fashion, SaaS, etc.\n\n"
                "Type /back if you want to change the previous answer."
            )
            return True

        if stage == "awaiting_challenge":
            update_profile(chat_id, state, stage="awaiting_goal")
            send_message(chat_id,
                "Okay, going back.\n\n"
                "3/5 — What is your main goal with social media right now?\n"
                "Example: Get more clients, Grow followers, Build authority, Sell a product, Increase engagement, etc.\n\n"
                "Type /back if you want to change the previous answer."
            )
            return True

        if stage == "awaiting_personality":
            update_profile(chat_id, state, stage="awaiting_challenge")
            send_message(chat_id,
                "Okay, going back.\n\n"
                "4/5 — What is the biggest challenge you're currently facing with content or growth?\n"
                "Example: Low engagement, Inconsistent posting, Not converting followers, Finding content ideas, Standing out, etc.\n\n"
                "Type /back if you want to change the previous answer."
            )
            return True

        send_message(chat_id, "There's nothing to go back to right now.")
        return True

    # Normal question flow
    if stage == "awaiting_brand_name":
        update_profile(chat_id, state, brand_name=text, stage="awaiting_niche")
        send_message(chat_id,
            f"Got it — {text}.\n\n"
            "2/5 — What niche or industry are you in?\n"
            "Example: Skincare, Fitness coaching, Personal branding, Real estate, Fashion, SaaS, etc.\n\n"
            "Type /back if you want to change the previous answer."
        )
        return True

    if stage == "awaiting_niche":
        update_profile(chat_id, state, niche=text, stage="awaiting_goal")
        send_message(chat_id,
            "Understood.\n\n"
            "3/5 — What is your main goal with social media right now?\n"
            "Example: Get more clients, Grow followers, Build authority, Sell a product, Increase engagement, etc.\n\n"
            "Type /back if you want to change the previous answer."
        )
        return True

    if stage == "awaiting_goal":
        update_profile(chat_id, state, goal=text, stage="awaiting_challenge")
        send_message(chat_id,
            "Clear.\n\n"
            "4/5 — What is the biggest challenge you're currently facing with content or growth?\n"
            "Example: Low engagement, Inconsistent posting, Not converting followers, Finding content ideas, Standing out, etc.\n\n"
            "Type /back if you want to change the previous answer."
        )
        return True

    if stage == "awaiting_challenge":
        update_profile(chat_id, state, challenge=text, stage="awaiting_personality")
        send_message(chat_id,
            "Thanks.\n\n"
            "5/5 — How would you describe your brand's personality or tone?\n"
            "Example: Humorous, Professional, Luxurious, Friendly, Bold, Educational, Chill, Motivational, etc.\n\n"
            "Type /back if you want to change the previous answer."
        )
        return True

    if stage == "awaiting_personality":
        update_profile(chat_id, state, personality=text, stage="complete")
        profile = get_profile(chat_id, state)
        send_message(chat_id,
            "Perfect. I now have everything I need.\n\n"
            f"{profile_summary(profile)}\n\n"
            "I can create personalized strategies and content for you from now on.\n\n"
            "What would you like to work on first?\n"
            "You can use /plan, /idea, /hooks, or just tell me what you need."
        )
        return True

    return False

def cmd_plan(chat_id: str, state: dict):
    context = build_context(chat_id, state)
    if "Not set" in context:
        send_message(chat_id, "I still need more information about your brand first. Let's do a quick /setup.")
        return

    send_message(chat_id, "Thinking about the best strategy for your brand...")
    prompt = (
        f"Here is the brand context:\n{context}\n\n"
        "Create a thoughtful, personalized weekly content strategy. "
        "Keep it practical and focused. Speak conversationally. "
        "End with one clear next step or question."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_idea(chat_id: str, args: List[str], state: dict):
    context = build_context(chat_id, state)
    extra = " ".join(args) if args else ""
    send_message(chat_id, "Coming up with something tailored for you...")
    prompt = (
        f"Brand context:\n{context}\n\n"
        f"Extra request: {extra}\n\n"
        "Give one strong, personalized post idea with a ready caption. "
        "Keep the response focused and natural."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_hooks(chat_id: str, args: List[str], state: dict):
    context = build_context(chat_id, state)
    topic = " ".join(args) if args else "their main niche"
    prompt = (
        f"Brand context:\n{context}\n\n"
        f"Generate 7 strong hooks related to: {topic}. "
        "Make them specific to this brand. Keep the tone natural."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_caption(chat_id: str, args: List[str], state: dict):
    context = build_context(chat_id, state)
    topic = " ".join(args) if args else "their main topic"
    prompt = (
        f"Brand context:\n{context}\n\n"
        f"Write 3 ready-to-post captions about: {topic}. "
        "Make them feel natural for this brand."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_calendar(chat_id: str, state: dict):
    context = build_context(chat_id, state)
    prompt = (
        f"Brand context:\n{context}\n\n"
        "Create a realistic 7-day content calendar tailored to this brand. "
        "Keep it practical and easy to follow."
    )
    result = generate(prompt, max_tokens=1100)
    send_message(chat_id, result)

def cmd_series(chat_id: str, args: List[str], state: dict):
    context = build_context(chat_id, state)
    topic = " ".join(args) if args else "their main theme"
    prompt = (
        f"Brand context:\n{context}\n\n"
        f"Propose 2 strong content series ideas around: {topic}. "
        "Make them relevant to this brand."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_tip(chat_id: str, state: dict):
    context = build_context(chat_id, state)
    prompt = (
        f"Brand context:\n{context}\n\n"
        "Give one sharp, personalized growth tip for this brand. Keep it short and useful."
    )
    result = generate(prompt, max_tokens=400)
    send_message(chat_id, result)

def cmd_trend(chat_id: str, state: dict):
    context = build_context(chat_id, state)
    prompt = (
        f"Brand context:\n{context}\n\n"
        "Share the most useful current trends and how this specific brand can use them."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_audit(chat_id: str, state: dict):
    context = build_context(chat_id, state)
    prompt = (
        f"Brand context:\n{context}\n\n"
        "Do a short, honest strategy audit. Point out likely weak spots and better approaches."
    )
    result = generate(prompt)
    send_message(chat_id, result)

def cmd_profile(chat_id: str, state: dict):
    profile = get_profile(chat_id, state)
    if not profile:
        send_message(chat_id, "I don't have any brand information yet. Type /setup to start.")
        return
    send_message(chat_id, f"Here's what I currently know about your brand:\n\n{profile_summary(profile)}")

def cmd_help(chat_id: str):
    send_message(chat_id, get_command_list())

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
        send_message(target, "You now have full access.")
    else:
        send_message(chat_id, f"{target} is already authorized.")

# ===================== MAIN LOOP =====================

def process_message(msg: dict, state: dict, users: dict):
    if "chat" not in msg or msg["chat"].get("type") != "private":
        return

    chat_id = str(msg["chat"]["id"])
    text = (msg.get("text") or "").strip()
    user = msg.get("from", {})
    name = user.get("first_name") or user.get("username") or "User"
    state["known_names"][chat_id] = name

    if not text:
        return

    # First check if we are in the middle of collecting brand info
    if handle_conversation(chat_id, text, state):
        return

    if not text.startswith("/"):
        # Free text — treat as conversation
        context = build_context(chat_id, state)
        prompt = (
            f"Brand context:\n{context}\n\n"
            f"User just said: {text}\n\n"
            "Respond as their senior social media manager. "
            "Be helpful, conversational, and ask a follow-up question if useful."
        )
        result = generate(prompt, max_tokens=600)
        send_message(chat_id, result)
        return

    parts = text.split()
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]

    network_cmds = {
        "/plan", "/idea", "/hooks", "/caption",
        "/calendar", "/series", "/tip", "/trend", "/audit"
    }
    if cmd in network_cmds:
        last = state["last_request_at"].get(chat_id, 0)
        if ts() - last < COOLDOWN_SECONDS:
            send_message(chat_id, "Give me a few seconds before the next request.")
            return
        state["last_request_at"][chat_id] = ts()

    if cmd in ("/start", "/help"):
        cmd_start(chat_id, text, state, users)
    elif cmd == "/setup":
        cmd_setup(chat_id, state)
    elif cmd == "/reset":
        cmd_reset(chat_id, state)
    elif cmd == "/plan":
        cmd_plan(chat_id, state)
    elif cmd == "/idea":
        cmd_idea(chat_id, args, state)
    elif cmd == "/hooks":
        cmd_hooks(chat_id, args, state)
    elif cmd == "/caption":
        cmd_caption(chat_id, args, state)
    elif cmd == "/calendar":
        cmd_calendar(chat_id, state)
    elif cmd == "/series":
        cmd_series(chat_id, args, state)
    elif cmd == "/tip":
        cmd_tip(chat_id, state)
    elif cmd == "/trend":
        cmd_trend(chat_id, state)
    elif cmd == "/audit":
        cmd_audit(chat_id, state)
    elif cmd == "/profile":
        cmd_profile(chat_id, state)
    elif cmd == "/authorize":
        cmd_authorize(chat_id, args, users, state)
    else:
        send_message(chat_id, "I didn't recognize that command. Type /help to see what I can do.")

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
