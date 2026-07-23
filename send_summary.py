import os
from openai import OpenAI, APIConnectionError
import requests
import datetime
import time

print("🔍 Starting SMM Summary...")

api_key = os.getenv("NVIDIA_API_KEY")
tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat = os.getenv("TELEGRAM_CHAT_ID")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key,
    timeout=60.0   # Increase timeout
)

for attempt in range(3):   # Retry up to 3 times
    try:
        print(f"🤖 Attempt {attempt+1}/3 - Calling NVIDIA NIM...")
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",   # Smaller, faster model for testing
            messages=[
                {"role": "system", "content": "You are an Expert Social Media Manager."},
                {"role": "user", "content": f"Today is {datetime.date.today()}. Give one short, actionable SMM tip."}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        print("✅ Successfully got response from NVIDIA")
        
        full_msg = f"🧠 **Expert SMM Update** — {datetime.date.today()}\n\n{summary}"
        
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        tg_response = requests.post(url, json={"chat_id": tg_chat, "text": full_msg, "parse_mode": "Markdown"})
        
        print(f"Telegram Status: {tg_response.status_code}")
        if tg_response.ok:
            print("✅ Message sent to Telegram!")
        break
            
    except APIConnectionError as e:
        print(f"❌ Connection failed (attempt {attempt+1}): {e}")
        if attempt < 2:
            time.sleep(5)  # Wait before retry
        else:
            print("❌ All attempts failed. NVIDIA may be unreachable from GitHub Actions right now.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        break
