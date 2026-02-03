import os
import httpx
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai_compatible")
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")


async def chat(message: str) -> str:
    if LLM_PROVIDER != "openai_compatible":
        raise ValueError("Unsupported LLM provider. Set LLM_PROVIDER=openai_compatible.")

    if not LLM_API_URL or not LLM_API_KEY or not LLM_MODEL:
        raise ValueError("LLM config missing. Set LLM_API_URL, LLM_API_KEY, LLM_MODEL.")

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are Daisy, a calm, helpful AI copilot. Keep responses concise and practical.",
            },
            {"role": "user", "content": message},
        ],
        "temperature": 0.6,
    }

    headers = {"Authorization": f"Bearer {LLM_API_KEY}"}

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(LLM_API_URL, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()

    return data["choices"][0]["message"]["content"]
