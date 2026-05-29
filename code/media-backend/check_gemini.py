import os
import httpx
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"Checking models using key: {GEMINI_API_KEY and GEMINI_API_KEY[:5]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"

try:
    resp = httpx.get(url, timeout=30)
    print("Status:", resp.status_code)
    data = resp.json()
    
    if "models" in data:
        print("\nAvailable Models for generateContent:")
        found_flash = False
        for m in data["models"]:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                name = m['name'].replace('models/', '')
                print(f" - {name}")
                if "flash" in name:
                    found_flash = True
        
        if not found_flash:
            print("\n⚠️ WARNING: No 'flash' model found. Use one of the above.")
    else:
        print("Response Error Body:", data)

except Exception as e:
    print("Request Failed:", e)
