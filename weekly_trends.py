import os
import json
from datetime import datetime
from agent import generate
from settings import TELEGRAM_BOT_TOKEN, STATE_FILE
from http_utils import request_with_retry
from time_utils import now_wat

def send_message(chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        request_with_retry("POST", url, json={
            "chat_id": str(chat_id),
            "text": text,
            "disable_web_page_preview": True
        })
        return True
    except Exception as e:
        print(f"Failed to send to {chat_id}: {e}")
        return False

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"profiles": {}}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("Starting weekly trends job...")
    state = load_state()
    profiles = state.get("profiles", {})

    sent = 0
    for chat_id, profile in profiles.items():
        if profile.get("stage") != "complete":
            continue
        if not profile.get("niche"):
            continue

        niche = profile.get("niche", "general")
        brand = profile.get("brand_name", "your brand")
        personality = profile.get("personality", "professional")
        goal = profile.get("goal", "growth")

        prompt = f"""
Brand: {brand}
Niche: {niche}
Goal: {goal}
Personality: {personality}

Write a short weekly trends report for this brand.
Focus on what is currently working in their niche on social media.
Keep it practical and useful (maximum 250-300 words).
Include:
- 2-3 relevant trends
- How this brand can use them this week
- One clear action they should take

Write in a natural, conversational tone. No markdown.
"""

        report = generate(prompt, max_tokens=700)

        message = (
            f"Weekly Trends Report for {brand}\n"
            f"Date: {now_wat().strftime('%d %b %Y')}\n\n"
            f"{report}\n\n"
            "Reply if you want me to turn any of these into content ideas."
        )

        if send_message(chat_id, message):
            sent += 1
            print(f"Sent to {chat_id}")

    print(f"Weekly trends job finished. Sent to {sent} users.")

if __name__ == "__main__":
    main()
