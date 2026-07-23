from openai import OpenAI
from config import NVIDIA_API_KEY, BASE_URL, MODEL, SYSTEM_PROMPT
import datetime

client = OpenAI(base_url=BASE_URL, api_key=NVIDIA_API_KEY)

async def generate_smm_response(user_query: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Date: {datetime.date.today()}\nQuery: {user_query}"}
            ],
            temperature=0.75,
            max_tokens=1600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ NVIDIA NIM Error: {str(e)}\nCheck your API key and rate limits."
