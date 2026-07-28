from openai import OpenAI, BadRequestError, APIConnectionError, AuthenticationError
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
from time_utils import now_wat

client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    timeout=60.0
)

SYSTEM_PROMPT = """You are a senior Social Media Manager with 10+ years of real experience.
You speak like a smart, direct colleague — not like a content dump machine.

Rules:
- Be conversational and thoughtful
- Ask clarifying questions when you need more context
- Keep answers focused and useful (avoid long walls of text)
- When you have enough information, give high-quality personalized advice
- Never use markdown, asterisks, or special formatting
- Sound human and experienced
"""

def generate(prompt: str, max_tokens: int = 900) -> str:
    if not NVIDIA_API_KEY or not NVIDIA_API_KEY.startswith("nvapi-"):
        return "NVIDIA API key is missing or invalid."

    try:
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Date: {now_wat().strftime('%Y-%m-%d')}\n\n{prompt}"
                }
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    except AuthenticationError:
        return "Authentication failed. Check your NVIDIA API key."
    except BadRequestError as e:
        return f"Bad request from NVIDIA: {str(e)}"
    except APIConnectionError:
        return "Could not connect to NVIDIA right now. Please try again shortly."
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {str(e)}"
