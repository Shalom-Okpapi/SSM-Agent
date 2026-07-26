from openai import OpenAI
from settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
from time_utils import now_wat

client = OpenAI(
    base_url=NVIDIA_BASE_URL,
    api_key=NVIDIA_API_KEY,
    timeout=45.0
)

SYSTEM_PROMPT = """You are an Expert Social Media Manager with 10+ years of real experience.
You are growth-focused, data-driven, creative and practical.
Always give clear, actionable advice with strong hooks and captions when relevant.
Be concise but complete. Use Markdown sparingly and correctly."""

def generate(prompt: str, max_tokens: int = 1200) -> str:
    try:
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Today is {now_wat().strftime('%Y-%m-%d')}.\n\n{prompt}"}
            ],
            temperature=0.72,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I hit an error talking to the AI: {type(e).__name__}"
