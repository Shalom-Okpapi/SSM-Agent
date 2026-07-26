from openai import OpenAI, BadRequestError, APIConnectionError, AuthenticationError
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
from time_utils import now_wat

client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    timeout=60.0
)

SYSTEM_PROMPT = """You are a senior Social Media Manager with 10+ years of experience growing accounts from zero to large audiences.

Your style:
- Extremely practical and specific
- Growth-focused (reach, engagement, saves, shares, follows)
- Platform-aware (Instagram, TikTok, LinkedIn, X, YouTube)
- You always give ready-to-use content, not vague advice
- You structure your answers clearly with headings and bullet points
- You sound confident, direct, and experienced — never generic or fluffy

When asked for ideas, always include:
- Strong hook
- Full caption (or script)
- Why it works
- Suggested format / CTA

Never give mid or average answers. Aim for content that actually has a chance to perform well."""

def generate(prompt: str, max_tokens: int = 1400) -> str:
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
            temperature=0.75,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    except AuthenticationError:
        return "Authentication failed. Check your NVIDIA API key."
    except BadRequestError as e:
        return f"Bad request from NVIDIA: {str(e)}"
    except APIConnectionError:
        return "Could not connect to NVIDIA. Please try again shortly."
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {str(e)}"
