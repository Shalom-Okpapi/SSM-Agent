import os
from openai import OpenAI
import requests
import datetime

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

def send_telegram(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("❌ Telegram credentials missing")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    })
    print(f"Telegram status: {response.status_code}")
    return response.ok

# Generate summary
try:
    print("🤖 Generating SMM summary...")
    response = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[
            {"role": "system", "content": "You are an Expert Social Media Manager."},
            {"role": "user", "content": f"Today is {datetime.date.today()}. Send a short, actionable daily/weekly SMM tip or quick strategy summary."}
        ],
        max_tokens=800,
        temperature=0.7
    )
    
    summary = response.choices[0].message.content
    full_message = f"🧠 **Expert SMM Daily Update** ({datetime.date.today()})\n\n{summary}"
    
    if send_telegram(full_message):
        print("✅ Summary sent to Telegram successfully!")
    else:
        print("❌ Failed to send to Telegram")
        
except Exception as e:
    print(f"❌ Error: {e}")
