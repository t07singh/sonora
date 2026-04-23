import os
from dotenv import load_dotenv
from transcriber import Transcriber

load_dotenv(override=True)

print("--- Environment Check ---")
print(f"CLOUD_OFFLOAD: {os.getenv('CLOUD_OFFLOAD')}")
print(f"GROQ_API_KEY: {'[SET]' if os.getenv('GROQ_API_KEY') else '[MISSING]'}")
print(f"GEMINI_API_KEY: {'[SET]' if os.getenv('GEMINI_API_KEY') else '[MISSING]'}")

print("\n--- ASR Transition Check ---")
t = Transcriber()
# Use a non-existent file to just check the branch logic
try:
    # This should fail on file not found, but we want to see which branch it takes
    t.transcribe("non_existent_file.mp3")
except Exception as e:
    print(f"Captured Error: {e}")
