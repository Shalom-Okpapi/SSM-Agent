import os
from openai import OpenAI
import requests
import datetime

print("🔍 Starting SMM Summary...")

# Check secrets
api_key = os.getenv("NVIDIA_API_KEY")
tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat = os.getenv("TELEGRAM_CHAT_ID")

print(f"NVIDIA Key present: {'Yes' if api_key and api_key.startswith('nvapi-') else 'No / Invalid'}")
print(f"Telegram Token present: {'Yes' if tg_token else 'No'}")
print(f"Telegram Chat ID present: {'Yes' if tg_chat else 'No'}")

if not api_key or not tg_token or not tg_chat:
    print("❌ Missing secrets!")
    exit(1)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

try:
    print("🤖 Calling NVIDIA NIM...")
    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are an Expert Social Media Manager."},
            {"role": "user", "content": f"Today is {datetime.date.today()}. Give a short, valuable SMM tip or quick strategy insight."}
        ],
        max_tokens=600,
        temperature=0.7
    )
    
    summary = response.choices[0].message.content.strip()
    print("✅ Got response from NVIDIA")
    
    full_msg = f"🧠 **Expert SMM Update** — {datetime.date.today()}\n\n{summary}"
    
    # Send to Telegram
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    tg_response = requests.post(url, json={
        "chat_id": tg_chat,
        "text": full_msg,
        "parse_mode": "Markdown"
    })
    
    print(f"Telegram Status: {tg_response.status_code}")
    if tg_response.ok:
        print("✅ Successfully sent to Telegram!")
    else:
        print(f"❌ Telegram failed: {tg_response.text}")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__} - {str(e)}")
