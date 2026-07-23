import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from agent import generate_smm_response
from config import TELEGRAM_BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Expert SMM Agent Bot** Ready!\n\n"
        "Commands:\n"
        "/plan → Weekly strategy\n"
        "/idea [platform niche] → Quick post idea + caption\n"
        "/help → Show commands"
    )

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Generating weekly SMM plan...")
    response = await generate_smm_response("Create a complete weekly social media content strategy with post ideas and captions.")
    await update.message.reply_text(response, parse_mode='Markdown')

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else "Instagram tech growth audience"
    await update.message.reply_text("💡 Generating idea...")
    prompt = f"High-engagement post idea + full caption for: {query}"
    response = await generate_smm_response(prompt)
    await update.message.reply_text(response, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("idea", idea))
    app.add_handler(CommandHandler("help", help_command))

    print("🤖 Expert SMM Telegram Bot started (polling)...")
    app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())  # Better for async
