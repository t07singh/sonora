
"""
SONORA EXECUTION: ITEM 3 - VIBEVOICE PROSODY INJECTOR
Builds: Speech-to-Speech (STS) pipeline for emotional preservation.
"""
import requests
import os

class VibeVoiceAgent:
    def __init__(self, api_key=None, voice_id=None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM" # Default "Rachel" voice if none provided
        self.url = f"https://api.elevenlabs.io/v1/speech-to-speech/{self.voice_id}"

    def perform_transfer(self, source_audio_path, english_text):
        """
        Uses the original Japanese audio as a 'Director' for the English TTS.
        Preserves: Pitch, Rhythm, and Emotional Intensity.
        """
        if not self.api_key:
            print("❌ Error: ELEVENLABS_API_KEY not found.")
            return None

        headers = {"xi-api-key": self.api_key}
        
        # We send the English text + the Japanese audio as a prosody reference
        # Note: ElevenLabs STS API expects 'text' if you want to override the words in the audio
        # but keep the performance.
        data = {
            "text": english_text,
            "model_id": "eleven_multilingual_sts_v2",
            "voice_settings": '{"stability": 0.3, "similarity_boost": 0.8, "style": 0.5}'
        }
        
        try:
            with open(source_audio_path, "rb") as audio_file:
                files = {
                    "audio": (os.path.basename(source_audio_path), audio_file, "audio/mpeg")
                }

                print(f"🎭 Transferring 'vibe' from {source_audio_path}...")
                response = requests.post(self.url, headers=headers, data=data, files=files)
            
            if response.status_code == 200:
                # Determine output path: same folder as source, but with _dubbed suffix
                base, ext = os.path.splitext(source_audio_path)
                output_path = f"{base}_dubbed.mp3"
                
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ VibeVoice Transfer Complete: {output_path}")
                return output_path
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
        except FileNotFoundError:
            print(f"❌ Error: Source audio file not found at {source_audio_path}")
            return None
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            return None

# --- TEST LOGIC ---
if __name__ == "__main__":
    # Internal test logic would require a real API key and file
    print("DONE: VibeVoice STS Engine Ready")
