import asyncio
import httpx
from app.config import settings

async def test():
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": "Hello"
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)

asyncio.run(test())
