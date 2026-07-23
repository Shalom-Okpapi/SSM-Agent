import os
import datetime
import json
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Config
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "meta/llama-3.1-70b-instruct"

client = OpenAI(base_url=BASE_URL, api_key=NVIDIA_API_KEY)

SYSTEM_PROMPT = """You are an Expert Social Media Manager with 10+ years experience. 
Focus on growth, engagement, virality, and conversions. 
Be strategic, creative, and data-driven. Always provide actionable advice."""

async def generate_response(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Current date: {datetime.date.today()}. User request: {user_message}"}
            ],
            temperature=0.75,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}\nTry again or check API key."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to **Expert SMM Agent**!\n\n"
        "I’m your 10-year veteran social media strategist.\n\n"
        "Commands:\n"
        "/plan → Full weekly strategy\n"
        "/idea [platform] [niche] → Quick post idea + caption\n"
        "/help → This message"
    )

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating your weekly SMM plan...")
    response = await generate_response("Create a complete weekly social media content strategy and post ideas.")
    await update.message.reply_text(response, parse_mode='Markdown')

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else "Instagram tech growth audience"
    await update.message.reply_text("💡 Generating post idea...")
    prompt = f"Give me a high-engagement post idea + full caption for: {query}"
    response = await generate_response(prompt)
    await update.message.reply_text(response, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("idea", idea))
    app.add_handler(CommandHandler("help", help_command))

    print("🤖 Expert SMM Telegram Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
