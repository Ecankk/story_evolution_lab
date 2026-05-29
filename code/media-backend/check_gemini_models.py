import os
from dotenv import load_dotenv
from google import genai

# Load env vars
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {api_key[:5]}...{api_key[-5:]}")
print("🔍 Querying Google GenAI for available models...")

try:
    client = genai.Client(api_key=api_key)
    
    print("--------------------------------------------------")
    count = 0
    for model in client.models.list():
        if "gemini" in model.name:
            print(f"- {model.name}")
            count += 1
    print("--------------------------------------------------")
            
    if count == 0:
        print("⚠️ No models found with generateContent support.")
    else:
        print(f"\n✨ Found {count} available models.")

except Exception as e:
    print(f"\n❌ Error listing models: {e}")
    print("Tip: Check if your API Key has the correct permissions or if you need to enable the API in Google Cloud Console.")
