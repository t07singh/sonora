
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print(f"DEBUG: GEMINI_API_KEY is {'set' if api_key else 'NOT SET'}")
if api_key:
    # Print first and last characters to verify without revealing the whole key
    print(f"DEBUG: Key starts with: {api_key[:4]}... and ends with: ...{api_key[-4:]}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print("DEBUG: Attempting to generate content...")
    response = model.generate_content("Translate 'Hello, how are you?' to Japanese. Respond only with the translation.")
    print(f"DEBUG: Success! Response: {response.text}")
except Exception as e:
    print(f"DEBUG: FAILED with error: {type(e).__name__}: {str(e)}")
