# =============================================================================
# SONORA STUDIO — Google Colab End-to-End Test Script
# =============================================================================
# Save this file as a .py, then open it in Google Colab as a notebook.
# Or copy-paste each cell block into a Colab notebook manually.
#
# GPU Runtime: Runtime > Change runtime type > T4 GPU
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# CELL 1: Check GPU & System Info
# ─────────────────────────────────────────────────────────────────────────────
import subprocess, sys

def run(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True)

print("=" * 60)
print("🚀 SONORA STUDIO — COLAB ENVIRONMENT CHECK")
print("=" * 60)

# GPU Check
gpu_info = run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
if gpu_info.returncode == 0:
    print(f"✅ GPU: {gpu_info.stdout.strip()}")
else:
    print("⚠️  No GPU detected — Running in CPU mode (slower)")

# Python version
print(f"✅ Python: {sys.version.split()[0]}")

# FFmpeg (pre-installed in Colab)
ffmpeg_check = run("ffmpeg -version")
if ffmpeg_check.returncode == 0:
    print(f"✅ FFmpeg: {ffmpeg_check.stdout.split()[2]}")
else:
    print("❌ FFmpeg missing")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 2: Clone Sonora Repository
# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: Replace with your actual GitHub repo URL
# If the repo is private, use: git clone https://<TOKEN>@github.com/...

import os

REPO_URL = "https://github.com/YOUR_USERNAME/sonora-studio.git"   # <-- UPDATE THIS
REPO_DIR = "/content/sonora-studio"

if not os.path.exists(REPO_DIR):
    print(f"📦 Cloning Sonora Studio from {REPO_URL}...")
    result = run(f"git clone {REPO_URL} {REPO_DIR}")
    if result.returncode == 0:
        print("✅ Repository cloned.")
    else:
        print(f"❌ Clone failed:\n{result.stderr}")
        print("\n💡 ALTERNATIVE: Upload the project as a .zip and unzip it:")
        print("   from google.colab import files; files.upload()")
        print("   !unzip sonora-studio.zip -d /content/sonora-studio")
else:
    print(f"✅ Repo already exists at {REPO_DIR}")

os.chdir(REPO_DIR)
sys.path.insert(0, REPO_DIR)
print(f"📁 Working directory: {os.getcwd()}")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 3: Install Core Dependencies
# ─────────────────────────────────────────────────────────────────────────────
print("\n📦 Installing Sonora Core Dependencies...")
print("(This may take 3-5 minutes on first run)\n")

# Core API & pipeline packages (lightweight, no local models)
core_packages = [
    "fastapi",
    "uvicorn[standard]",
    "httpx",
    "pydantic>=2.0.0",
    "python-dotenv",
    "python-multipart",
    "aiofiles",

    # Cloud providers
    "groq>=0.4.0",
    "openai>=1.0.0",
    "google-generativeai>=0.3.0",
    "elevenlabs>=1.0.0",
    "requests",

    # Audio
    "librosa",
    "soundfile",
    "numpy<2.0.0",
    "scipy",

    # Gradio client for HF Spaces
    "gradio_client>=0.10.0",
    "huggingface_hub",

    # New additions
    "scenedetect[opencv]",   # OmniShotCut local fallback
    "tenacity",              # Retry/backoff

    # Observability
    "psutil",
    "tqdm",
]

for pkg in core_packages:
    result = run(f"pip install -q {pkg}")
    status = "✅" if result.returncode == 0 else "❌"
    print(f"  {status} {pkg}")

print("\n✅ Core packages installed.")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 4: Configure API Keys (Using Colab Secrets)
# ─────────────────────────────────────────────────────────────────────────────
# In Colab: Click the 🔑 (key icon) in the left sidebar → "Secrets"
# Add keys: GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, HF_TOKEN, FISHAUDIO_API_KEY

import os

def load_colab_secrets():
    """Load API keys from Colab Secrets (userdata) or environment."""
    try:
        from google.colab import userdata
        secrets = {
            "GROQ_API_KEY":       userdata.get("GROQ_API_KEY"),
            "GEMINI_API_KEY":     userdata.get("GEMINI_API_KEY"),
            "OPENAI_API_KEY":     userdata.get("OPENAI_API_KEY"),
            "HF_TOKEN":           userdata.get("HF_TOKEN"),
            "FISHAUDIO_API_KEY":  userdata.get("FISHAUDIO_API_KEY"),
            "ELEVENLABS_API_KEY": userdata.get("ELEVENLABS_API_KEY"),
        }
        for k, v in secrets.items():
            if v:
                os.environ[k] = v
        print("✅ API keys loaded from Colab Secrets.")
    except Exception:
        # Fallback: set keys manually here for testing
        print("⚠️  Could not load Colab Secrets. Setting keys manually...")
        print("    → Add your keys below or use Colab Secrets sidebar (🔑)")

load_colab_secrets()

# ── MANUAL KEY OVERRIDE (only if Secrets not configured) ──────────────────
# Uncomment and fill in ONLY if you are not using Colab Secrets:
# os.environ["GROQ_API_KEY"] = "gsk_..."
# os.environ["GEMINI_API_KEY"] = "AIza..."
# os.environ["OPENAI_API_KEY"] = "sk-..."
# os.environ["HF_TOKEN"] = "hf_..."
# os.environ["FISHAUDIO_API_KEY"] = "..."

# Sonora config
os.environ["CLOUD_OFFLOAD"] = "true"
os.environ["SHARED_PATH"] = "/content/sonora_data"
os.environ["SONORA_DATA_DIR"] = "/content/sonora_data"
os.makedirs("/content/sonora_data", exist_ok=True)

print("\n📋 Active Environment:")
for key in ["GROQ_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "HF_TOKEN", "FISHAUDIO_API_KEY"]:
    val = os.environ.get(key, "")
    status = "✅ Set" if val else "⚠️  Missing"
    print(f"  {status}: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 5: Run Full Diagnostics Suite
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🔬 SONORA DIAGNOSTICS: Testing All 8 Components")
print("=" * 60)

results = {}

# [1/8] FFmpeg
print("\n🔍 [1/8] FFmpeg Engine...")
try:
    r = run("ffmpeg -version")
    assert r.returncode == 0
    print("✅ FFmpeg: OK")
    results["ffmpeg"] = True
except:
    print("❌ FFmpeg: FAILED")
    results["ffmpeg"] = False

# [2/8] Groq API
print("\n🔍 [2/8] Groq API (High-Speed ASR)...")
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        models = client.models.list()
        print(f"✅ Groq API: OK ({len(list(models.data))} models available)")
        results["groq"] = True
    except Exception as e:
        print(f"❌ Groq API: FAILED\n  Error: {e}")
        results["groq"] = False
else:
    print("⚠️  Groq API: SKIPPED (No key)")
    results["groq"] = None

# [3/8] Gemini API
print("\n🔍 [3/8] Gemini API (Translator)...")
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        print(f"✅ Gemini API: OK ({len(models)} models)")
        results["gemini"] = True
    except Exception as e:
        print(f"❌ Gemini API: FAILED\n  Error: {e}")
        results["gemini"] = False
else:
    print("⚠️  Gemini API: SKIPPED (No key)")
    results["gemini"] = None

# [4/8] HF Spaces (Shadow Network)
print("\n🔍 [4/8] HF Spaces (Shadow Network)...")
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    try:
        from gradio_client import Client
        client = Client("facebook/demucs", hf_token=hf_token)
        print("✅ HF Spaces (Demucs): Online")
        results["hf_spaces"] = True
    except Exception as e:
        print(f"❌ HF Spaces: FAILED\n  Error: {e}")
        results["hf_spaces"] = False
else:
    print("⚠️  HF Spaces: SKIPPED (No HF_TOKEN)")
    results["hf_spaces"] = None

# [5/8] OmniShotCut (SceneDetect fallback)
print("\n🔍 [5/8] OmniShotCut Visual Slicer (PySceneDetect)...")
try:
    from scenedetect import detect, AdaptiveDetector
    print("✅ PySceneDetect: OK (OmniShotCut fallback ready)")
    results["omnishotcut"] = True
except Exception as e:
    print(f"❌ OmniShotCut: FAILED\n  Error: {e}")
    results["omnishotcut"] = False

# [6/8] Fish Audio S2
print("\n🔍 [6/8] Fish Audio S2 (Primary TTS)...")
fish_key = os.getenv("FISHAUDIO_API_KEY")
if fish_key:
    try:
        r = __import__("requests").get(
            "https://api.fish.audio/v1/models",
            headers={"Authorization": f"Bearer {fish_key}"}
        )
        r.raise_for_status()
        print(f"✅ Fish Audio S2: OK ({len(r.json())} models available)")
        results["fish_audio"] = True
    except Exception as e:
        print(f"❌ Fish Audio S2: FAILED\n  Error: {e}")
        results["fish_audio"] = False
else:
    print("⚠️  Fish Audio S2: SKIPPED (No FISHAUDIO_API_KEY)")
    results["fish_audio"] = None

# [7/8] ElevenLabs (Fallback TTS)
print("\n🔍 [7/8] ElevenLabs (Fallback TTS)...")
el_key = os.getenv("ELEVENLABS_API_KEY")
if el_key:
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=el_key)
        try: client.models.get_all()
        except AttributeError: client.voices.get_all()
        print("✅ ElevenLabs: OK")
        results["elevenlabs"] = True
    except Exception as e:
        print(f"❌ ElevenLabs: FAILED\n  Error: {e}")
        results["elevenlabs"] = False
else:
    print("⚠️  ElevenLabs: SKIPPED (No key)")
    results["elevenlabs"] = None

# [8/8] OpenAI (Ultimate Fallback)
print("\n🔍 [8/8] OpenAI API (Fallback Chain)...")
oai_key = os.getenv("OPENAI_API_KEY")
if oai_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=oai_key)
        client.models.list()
        print("✅ OpenAI: OK")
        results["openai"] = True
    except Exception as e:
        print(f"❌ OpenAI: FAILED\n  Error: {e}")
        results["openai"] = False
else:
    print("⚠️  OpenAI: SKIPPED (No key)")
    results["openai"] = None

# Summary
print("\n" + "=" * 60)
passed = sum(1 for v in results.values() if v is True)
failed = sum(1 for v in results.values() if v is False)
skipped = sum(1 for v in results.values() if v is None)
print(f"📊 DIAGNOSTICS: {passed} passed | {failed} failed | {skipped} skipped")
if failed == 0:
    print("🎉 ALL ACTIVE COMPONENTS HEALTHY — PIPELINE READY")
else:
    print("⚠️  SOME ISSUES DETECTED — CHECK ABOVE ERRORS")
print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# CELL 6: Test 1 — ASR Pipeline (Groq Whisper on a sample audio)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 TEST 1: Groq Whisper ASR (High-Speed Transcription)")
print("=" * 60)

# Download a short public-domain Japanese audio sample for testing
TEST_AUDIO_URL = "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"  # Replace with anime audio
TEST_AUDIO_PATH = "/content/test_audio.wav"

# Download test audio
run(f"wget -q -O {TEST_AUDIO_PATH} {TEST_AUDIO_URL}")
print(f"📥 Test audio downloaded: {TEST_AUDIO_PATH}")

groq_key = os.getenv("GROQ_API_KEY")
if groq_key and os.path.exists(TEST_AUDIO_PATH):
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        with open(TEST_AUDIO_PATH, "rb") as f:
            result = client.audio.transcriptions.create(
                file=("test.wav", f),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        print(f"✅ Transcription: '{result.text[:200]}'")
        print(f"   Language detected: {getattr(result, 'language', 'N/A')}")
        print(f"   Segments: {len(getattr(result, 'segments', []))}")
    except Exception as e:
        print(f"❌ ASR Test failed: {e}")
else:
    print("⚠️  Skipping ASR test (No GROQ_API_KEY or audio file)")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 7: Test 2 — Translation Pipeline (Gemini)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 TEST 2: Gemini Translation (Syllable-Aware)")
print("=" * 60)

SAMPLE_JP = "俺はナルト・ウズマキ！"  # "I am Naruto Uzumaki!"
TARGET_SYLLABLES = 8

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        prompt = f"""You are a professional anime dubbing translator.
Translate the following Japanese text to English for voice dubbing.
Target syllable count: {TARGET_SYLLABLES} syllables.
Match the emotional energy of the original.
Output ONLY the translated line, no explanation.

Japanese: {SAMPLE_JP}"""

        response = model.generate_content(prompt)
        translation = response.text.strip()
        print(f"✅ Source (JP): {SAMPLE_JP}")
        print(f"   Translation: {translation}")
        print(f"   Target syllables: {TARGET_SYLLABLES}")
    except Exception as e:
        print(f"❌ Translation Test failed: {e}")
else:
    print("⚠️  Skipping Translation test (No GEMINI_API_KEY)")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 8: Test 3 — Fish Audio S2 TTS (Main Character Voice)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 TEST 3: Fish Audio S2 (Primary TTS Engine)")
print("=" * 60)

import requests, io, soundfile as sf

TEST_TEXT = "I am Naruto Uzumaki! Believe it!"
FISH_API_KEY = os.getenv("FISHAUDIO_API_KEY")

if FISH_API_KEY:
    try:
        response = requests.post(
            "https://api.fish.audio/v1/tts",
            headers={
                "Authorization": f"Bearer {FISH_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "text": TEST_TEXT,
                "format": "wav",
                "latency": "balanced",
            },
            timeout=30
        )
        response.raise_for_status()

        # Save and display audio
        output_path = "/content/test_fish_s2.wav"
        with open(output_path, "wb") as f:
            f.write(response.content)

        audio, sr = sf.read(output_path)
        duration = len(audio) / sr
        print(f"✅ Fish Audio S2: Generated {duration:.2f}s of audio")
        print(f"   File: {output_path}")
        print(f"   Sample Rate: {sr}Hz | Samples: {len(audio)}")

        # Playback in Colab
        from IPython.display import Audio, display
        display(Audio(output_path))

    except Exception as e:
        print(f"❌ Fish Audio Test failed: {e}")
else:
    print("⚠️  Skipping Fish Audio test (No FISHAUDIO_API_KEY)")
    print("   → Register at https://fish.audio to get an API key")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 9: Test 4 — OmniShotCut (Visual Scene Detection)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 TEST 4: OmniShotCut — PySceneDetect (Visual Slicer)")
print("=" * 60)

# Download a short test video
TEST_VIDEO_URL = "https://www.pexels.com/video/853889/download/?fps=25.0&h=240&w=426"
TEST_VIDEO_PATH = "/content/test_video.mp4"

print("📥 Downloading test video...")
run(f"wget -q -O {TEST_VIDEO_PATH} '{TEST_VIDEO_URL}'")

if os.path.exists(TEST_VIDEO_PATH):
    try:
        from scenedetect import detect, AdaptiveDetector

        print("🎬 Detecting visual shot boundaries...")
        scenes = detect(TEST_VIDEO_PATH, AdaptiveDetector())
        boundaries = [scene[0].get_seconds() for scene in scenes[1:]]

        print(f"✅ Detected {len(boundaries)} visual shot boundaries:")
        for i, ts in enumerate(boundaries[:10]):  # Show first 10
            print(f"   Cut {i+1}: {ts:.3f}s")
        if len(boundaries) > 10:
            print(f"   ... and {len(boundaries) - 10} more")

    except Exception as e:
        print(f"❌ OmniShotCut Test failed: {e}")
else:
    print("⚠️  Test video not available — skipping scene detection test")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 10: Test 5 — HF Shadow Network (Demucs Audio Separation)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 TEST 5: HF Shadow Network (Demucs Vocal Separation)")
print("=" * 60)

hf_token = os.getenv("HF_TOKEN")
if hf_token and os.path.exists(TEST_AUDIO_PATH):
    try:
        from gradio_client import Client, handle_file
        print("🔗 Connecting to HF Space: facebook/demucs...")
        client = Client("facebook/demucs", hf_token=hf_token)

        print("🎵 Running vocal separation (may take 30-60s)...")
        result = client.predict(
            audio=handle_file(TEST_AUDIO_PATH),
            model="htdemucs",
            api_name="/predict"
        )
        print(f"✅ Demucs: Separation complete")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ HF Shadow Network Test failed: {e}")
        print(f"   Tip: The space may be sleeping — try again in 2 minutes")
else:
    print("⚠️  Skipping Demucs test (No HF_TOKEN or test audio)")


# ─────────────────────────────────────────────────────────────────────────────
# CELL 11: Full End-to-End Mini Pipeline
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("🧪 FULL END-TO-END PIPELINE TEST (Mini)")
print("=" * 60)
print("Simulating: JP Audio → Transcribe → Translate → Synthesize")
print()

# Step 1: Transcribe
print("Step 1/3: 🎤 Transcription (Groq Whisper)...")
groq_key = os.getenv("GROQ_API_KEY")
transcript_text = "俺はナルト・ウズマキ！"  # Fallback if Groq is missing

if groq_key and os.path.exists(TEST_AUDIO_PATH):
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        with open(TEST_AUDIO_PATH, "rb") as f:
            result = client.audio.transcriptions.create(
                file=("test.wav", f), model="whisper-large-v3", response_format="text"
            )
        transcript_text = result.strip() or transcript_text
        print(f"   ✅ Transcribed: '{transcript_text}'")
    except Exception as e:
        print(f"   ⚠️  Groq failed ({e}), using sample text")
else:
    print(f"   ⚠️  Using sample text: '{transcript_text}'")

# Step 2: Translate
print("Step 2/3: 🌐 Translation (Gemini)...")
translation = "I am Naruto Uzumaki! Believe it!"  # Fallback

gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f"Translate to natural English for anime dubbing (8 syllables max): {transcript_text}\nOutput only the translation."
        resp = model.generate_content(prompt)
        translation = resp.text.strip() or translation
        print(f"   ✅ Translated: '{translation}'")
    except Exception as e:
        print(f"   ⚠️  Gemini failed ({e}), using fallback translation")
else:
    print(f"   ⚠️  Using fallback: '{translation}'")

# Step 3: Synthesize
print("Step 3/3: 🎙️ Synthesis (Fish Audio S2 / ElevenLabs)...")
fish_key = os.getenv("FISHAUDIO_API_KEY")
el_key = os.getenv("ELEVENLABS_API_KEY")

if fish_key:
    try:
        import requests, soundfile as sf
        resp = requests.post(
            "https://api.fish.audio/v1/tts",
            headers={"Authorization": f"Bearer {fish_key}", "Content-Type": "application/json"},
            json={"text": translation, "format": "wav"},
            timeout=30
        )
        resp.raise_for_status()
        final_audio = "/content/sonora_final_output.wav"
        with open(final_audio, "wb") as f: f.write(resp.content)
        audio, sr = sf.read(final_audio)
        print(f"   ✅ Fish S2 synthesized: {len(audio)/sr:.2f}s audio")
        from IPython.display import Audio, display
        display(Audio(final_audio))
    except Exception as e:
        print(f"   ❌ Fish S2 failed: {e}")
elif el_key:
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=el_key)
        audio_gen = client.text_to_speech.convert(
            voice_id="JBFqnCBcs6BaNtIGwHQK",
            text=translation,
            model_id="eleven_flash_v2_5"
        )
        final_audio = "/content/sonora_final_output.wav"
        with open(final_audio, "wb") as f:
            for chunk in audio_gen: f.write(chunk)
        print(f"   ✅ ElevenLabs synthesized output")
        from IPython.display import Audio, display
        display(Audio(final_audio))
    except Exception as e:
        print(f"   ❌ ElevenLabs failed: {e}")
else:
    print("   ⚠️  No TTS API key — skipping synthesis")

print()
print("=" * 60)
print("🎉 PIPELINE TEST COMPLETE")
print(f"   Source text: '{transcript_text}'")
print(f"   Translation: '{translation}'")
print("=" * 60)
