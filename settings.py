import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = str(os.getenv("ADMIN_CHAT_ID", "")).strip()

# NVIDIA NIM
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct").strip()

# Bot behaviour
DM_POLL_WINDOW_SECONDS = int(os.getenv("DM_POLL_WINDOW_SECONDS", "240"))
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
COOLDOWN_SECONDS = 8          # only for network-heavy commands

# Files
STATE_FILE = "smm_state.json"
USERS_FILE = "authorized_users.json"

# Business
BOT_NAME = "Expert SMM Agent"
MONTHLY_PRICE = "Free"        # change later if you want to charge
