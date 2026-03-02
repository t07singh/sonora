
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print(f"DEBUG: GEMINI_API_KEY is {'set' if api_key else 'NOT SET'}")
if api_key:
    print(f"DEBUG: Key starts with: {api_key[:4]}... and ends with: ...{api_key[-4:]}")

try:
    genai.configure(api_key=api_key)
    
    print("\n--- Listing Available Models ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"ID: {m.name} | Display Name: {m.display_name}")
    
    # Try a few common variations
    test_models = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro"]
    
    print("\n--- Probing Specific Models ---")
    for model_name in test_models:
        try:
            print(f"DEBUG: Testing model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
            print(f"  ✅ SUCCESS: {model_name}")
            break
        except Exception as e:
            print(f"  ❌ FAILED: {model_name} | Error: {str(e)[:100]}")
            
except Exception as e:
    print(f"DEBUG: GLOBAL FAILURE: {type(e).__name__}: {str(e)}")
