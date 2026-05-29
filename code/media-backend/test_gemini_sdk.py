import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"Testing Gemini SDK with key: {GEMINI_API_KEY[:5]}...")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Explain how AI works in a few words"
    )
    print("\n[SUCCESS] Response:")
    print(response.text)
except Exception as e:
    print(f"\n[FAILED] {e}")
