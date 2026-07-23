import os
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # For notifications

BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "meta/llama-3.1-70b-instruct"

SYSTEM_PROMPT = """You are an Expert Social Media Manager with 10+ years of experience.
Growth-focused, data-driven, creative, and strategic.
Always deliver actionable plans, strong hooks, captions, and recommendations."""
