import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from agent import generate_smm_response
from config import TELEGRAM_BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """👋 Welcome back, Opps!

Here's what I can do as your Expert Social Media Manager:

• /plan — Get full weekly content strategy + post ideas
• /idea [platform] [niche] — Quick high-engagement post idea + caption (e.g. /idea instagram fitness)
• /caption [topic] — Generate ready-to-post captions
• /trend — Current social media trends & opportunities
• /tip — Quick daily growth tip

You can also just type a topic and I'll give you smart SMM advice.

I help with: Instagram, LinkedIn, Twitter/X, TikTok, YouTube.

⚠️ I'm an AI strategist — I give advice only. Always review before posting."""

    await update.message.reply_text(welcome)

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating your weekly SMM plan...")
    response = await generate_smm_response("Create a complete weekly social media content strategy with multiple post ideas and captions.")
    await update.message.reply_text(response, parse_mode='Markdown')

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else "Instagram tech growth audience"
    await update.message.reply_text("💡 Generating post idea...")
    prompt = f"Give me a strong post idea with full caption for: {query}"
    response = await generate_smm_response(prompt)
    await update.message.reply_text(response, parse_mode='Markdown')

async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💡 Quick tip coming...")
    response = await generate_smm_response("Give one actionable daily social media growth tip.")
    await update.message.reply_text(response, parse_mode='Markdown')

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("idea", idea))
    app.add_handler(CommandHandler("tip", tip))

    print("🤖 Expert SMM Telegram Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
