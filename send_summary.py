import os
import requests
import json
import datetime
import time

print("🔍 Starting SMM Summary...")

API_KEY = os.getenv("NVIDIA_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")

if not API_KEY or not TG_TOKEN or not TG_CHAT:
    print("❌ Missing secrets!")
    exit(1)

url = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [
        {"role": "system", "content": "You are an Expert Social Media Manager."},
        {"role": "user", "content": f"Today is {datetime.date.today()}. Give one short, valuable SMM tip or insight."}
    ],
    "max_tokens": 600,
    "temperature": 0.7
}

for attempt in range(3):
    try:
        print(f"🤖 Attempt {attempt+1}/3 - Calling NVIDIA...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            summary = data['choices'][0]['message']['content'].strip()
            print("✅ Got response from NVIDIA")
            
            full_msg = f"🧠 **Expert SMM Update** — {datetime.date.today()}\n\n{summary}"
            
            tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            tg_resp = requests.post(tg_url, json={
                "chat_id": TG_CHAT,
                "text": full_msg,
                "parse_mode": "Markdown"
            })
            
            print(f"Telegram Status: {tg_resp.status_code}")
            if tg_resp.ok:
                print("✅ Successfully sent to Telegram!")
            break
        else:
            print(f"❌ NVIDIA Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection failed (attempt {attempt+1}): {e}")
        if attempt < 2:
            time.sleep(8)
        else:
            print("❌ All attempts failed.")
