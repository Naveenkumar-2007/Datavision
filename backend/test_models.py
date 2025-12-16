"""
Test OpenRouter AI Models - Verify which ones actually work
"""
import asyncio
import aiohttp
import os

# Load API key from .env
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

# Models to test
MODELS_TO_TEST = [
    ("deepseek-chat", "deepseek/deepseek-chat"),
    ("deepseek-coder", "deepseek/deepseek-coder"),
    ("mistral-7b", "mistralai/mistral-7b-instruct:free"),
    ("llama-70b", "meta-llama/llama-3.3-70b-instruct:free"),
    ("gpt-oss", "openai/gpt-oss-120b:free"),
    ("gemini-flash", "google/gemini-2.0-flash-exp:free"),
]

async def test_model(name: str, model_id: str) -> dict:
    """Test a single model"""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": "Say 'Hello, I am working!' in one line."}
        ],
        "max_tokens": 50,
        "temperature": 0.1,
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-business-analyst.app",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {"name": name, "model_id": model_id, "status": "✅ WORKING", "response": content[:50]}
                else:
                    error = await response.text()
                    return {"name": name, "model_id": model_id, "status": f"❌ ERROR {response.status}", "response": error[:100]}
    except Exception as e:
        return {"name": name, "model_id": model_id, "status": "❌ EXCEPTION", "response": str(e)[:50]}

async def main():
    print("=" * 60)
    print("TESTING OPENROUTER MODELS")
    print("=" * 60)
    print(f"API Key: {API_KEY[:20]}..." if API_KEY else "NO API KEY!")
    print()
    
    results = []
    for name, model_id in MODELS_TO_TEST:
        print(f"Testing {name}...", end=" ", flush=True)
        result = await test_model(name, model_id)
        results.append(result)
        print(result["status"])
    
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    working = []
    not_working = []
    
    for r in results:
        if "WORKING" in r["status"]:
            working.append(r["name"])
            print(f"✅ {r['name']}: {r['model_id']}")
        else:
            not_working.append(r["name"])
            print(f"❌ {r['name']}: {r['status']}")
    
    print()
    print(f"WORKING MODELS ({len(working)}): {', '.join(working) if working else 'None'}")
    print(f"NOT WORKING ({len(not_working)}): {', '.join(not_working) if not_working else 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
