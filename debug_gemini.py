import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("CRITICAL ERROR: GEMINI_API_KEY not found in environment!")
    print("Environment variables found:")
    for k in os.environ.keys():
        if "KEY" in k or "SONORA" in k:
            print(f"- {k}")
else:
    print(f"Testing Gemini API Key: {api_key[:10]}...")

try:
    print("Configuring Google Generative AI...")
    genai.configure(api_key=api_key)
    print("Querying for available models...")
    models = list(genai.list_models())
    if not models:
        print("WARNING: No models returned from genai.list_models()")
    else:
        print(f"Found {len(models)} total models. Filtering for 'generateContent' support:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
            else:
                print(f"❌ {m.name} (methods: {m.supported_generation_methods})")
except Exception as e:
    print(f"SYSTEM FAILURE: {e}")
    import traceback
    traceback.print_exc()
