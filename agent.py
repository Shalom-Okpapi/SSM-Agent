from openai import OpenAI, BadRequestError, APIConnectionError, AuthenticationError
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
from time_utils import now_wat

client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    timeout=60.0
)

SYSTEM_PROMPT = (
    "You are an Expert Social Media Manager with 10+ years of real experience. "
    "You are growth-focused, data-driven, creative and practical. "
    "Always give clear, actionable advice with strong hooks and captions when relevant. "
    "Be concise but complete."
)

def generate(prompt: str, max_tokens: int = 1100) -> str:
    if not NVIDIA_API_KEY or not NVIDIA_API_KEY.startswith("nvapi-"):
        return "NVIDIA API key is missing or invalid. Please check the secret."

    try:
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Today is {now_wat().strftime('%Y-%m-%d')}.\n\n{prompt}"
                }
            ],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    except AuthenticationError:
        return "Authentication failed. Your NVIDIA API key is invalid or expired."

    except BadRequestError as e:
        # This is the most common error – surface the real message
        err = str(e)
        if "model" in err.lower():
            return f"Bad request – model issue. Current model: {NVIDIA_MODEL}\nError: {err}"
        return f"Bad request from NVIDIA: {err}"

    except APIConnectionError:
        return "Could not connect to NVIDIA. Try again in a moment."

    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {str(e)}"
