# 🧪 Sonora Integration & Efficiency Test Plan

This comprehensive test plan validates both **functionality** and **efficiency** of all integrated open models (offline + hybrid) in the Sonora API backend.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Overview](#test-overview)
3. [Individual Tests](#individual-tests)
4. [Benchmark Suite](#benchmark-suite)
5. [Debugging Guide](#debugging-guide)
6. [Expected Outcomes](#expected-outcomes)

---

## 🚀 Quick Start

### Prerequisites

1. **Start the Sonora API server:**
   ```bash
   cd sonora
   python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
   ```

2. **Run all tests:**
   ```bash
   python sonora/scripts/run_tests.py
   ```

3. **Run specific test:**
   ```bash
   python sonora/scripts/run_tests.py --test 1
   ```

4. **Run benchmark:**
   ```bash
   python sonora/scripts/benchmark_tts_translation.py
   ```

---

## 📊 Test Overview

| Test | Name | Goal | Expected Duration |
|------|------|------|-------------------|
| 1 | API Health & Boot Diagnostics | Confirm API and modules initialize correctly | < 5s |
| 2 | Offline Translation (Hugging Face) | Verify translation works efficiently | < 6s (cold), < 1s (warm) |
| 3 | Offline TTS (Coqui) | Confirm Coqui TTS produces clear audio | < 4s (CPU), < 2s (GPU) |
| 4 | VibeVoice Integration | Verify VibeVoice synthesizes correctly | < 3s |
| 5 | Emotion Detection & Propagation | Ensure emotion detection works | < 30s |
| 6 | End-to-End Dubbing Flow | Verify full pipeline works | < 5min |
| 7 | Efficiency Benchmark | Measure performance across providers | ~10min |

---

## 🧩 Individual Tests

### TEST 1 — API Health & Boot Diagnostics

**Goal:** Confirm API and modules initialize correctly.

**Command:**
```bash
curl http://127.0.0.1:8000/health
```

**Or Python:**
```python
python sonora/scripts/run_tests.py --test 1
```

**Expected Output:**
```json
{
  "status": "ok",
  "uptime": 123.45,
  "translation": "local",
  "tts": "coqui/vibevoice",
  "components": {
    "transcriber": true,
    "translator": true,
    "tts_provider": true,
    "cache_manager": true
  }
}
```

**✅ Pass Criteria:**
- Status is "ok"
- All components are `true`
- Uptime is a positive number

**❌ Failure Indicators:**
- Status code != 200
- Components show `false`
- Missing expected fields

---

### TEST 2 — Offline Translation (Hugging Face)

**Goal:** Verify the Hugging Face translation module works and responds efficiently.

**Script:**
```python
python sonora/scripts/run_tests.py --test 2
```

**Or Python API:**
```python
import requests

payload = {
    "text": "これはテストです。",
    "source_lang": "ja",
    "target_lang": "en"
}

response = requests.post("http://127.0.0.1:8000/api/translate", json=payload)
print(response.json())
```

**Expected Output:**
```json
{
  "translated_text": "This is a test.",
  "source_lang": "ja",
  "target_lang": "en",
  "processing_time": 0.85
}
```

**Efficiency Metrics:**
- **Cold start:** < 6 seconds (first model load)
- **Warm inference:** < 1 second for short text

**✅ Pass Criteria:**
- Translation works
- Latency within acceptable range
- Translation quality is reasonable (not gibberish)

**❌ Failure Indicators:**
- Hangs or timeout
- Translation returns Japanese text unchanged
- Error status codes

**Debug Steps:**
- Check `local_translator.py` logs
- Ensure model downloaded: `Helsinki-NLP/opus-mt-ja-en`
- Check Hugging Face transformers installation

---

### TEST 3 — Offline TTS (Coqui)

**Goal:** Confirm Coqui TTS produces clear, correctly-timed audio and emotion mapping works.

**Script:**
```python
python sonora/scripts/run_tests.py --test 3
```

**Or Python API:**
```python
import requests

payload = {
    "text": "Hello, this is Sonora speaking with emotion.",
    "provider": "coqui",
    "emotion": "excited"
}

response = requests.post("http://127.0.0.1:8000/api/tts/generate", json=payload)
with open("test_coqui.wav", "wb") as f:
    f.write(response.content)
```

**Expected Result:**
- A playable audio file with clear tone
- Emotion "excited" increases pitch/speed slightly
- Audio duration matches text length (±10%)

**Efficiency Metrics:**
- **Generation time:** < 4 seconds for short text (CPU)
- **GPU:** < 2 seconds

**✅ Pass Criteria:**
- Audio file generated successfully
- Audio is playable
- Emotion affects voice characteristics
- Processing time within acceptable range

**❌ Failure Indicators:**
- Error status codes
- No audio file generated
- Audio file is corrupted or empty

**Debug Steps:**
- Check `coqui_tts.py` logs
- Verify Coqui TTS installation: `pip install TTS`
- Check model download status
- Verify ffmpeg is installed

---

### TEST 4 — VibeVoice Integration Check

**Goal:** Verify that VibeVoice still initializes and synthesizes audio correctly post-migration.

**Script:**
```python
python sonora/scripts/run_tests.py --test 4
```

**Or Python API:**
```python
import requests

payload = {
    "text": "Testing the VibeVoice engine performance.",
    "provider": "vibevoice",
    "emotion": "neutral"
}

response = requests.post("http://127.0.0.1:8000/api/tts/generate", json=payload)
with open("test_vibevoice.wav", "wb") as f:
    f.write(response.content)
```

**Expected:**
- Clean, natural voice
- Timing similar to Coqui's TTS (or faster)
- Emotion-neutral sound

**Efficiency Metrics:**
- **Generation time:** < 3 seconds
- **Audio duration:** Matches text duration (±10%)

**✅ Pass Criteria:**
- Audio clarity good
- Speed acceptable
- No errors

**❌ Failure Indicators:**
- VibeVoice backend errors
- Socket or model load errors
- Timeout

**Debug Steps:**
- Check VibeVoice backend logs
- Verify VibeVoice installation
- Check model paths

---

### TEST 5 — Emotion Detection & Propagation

**Goal:** Ensure SpeechBrain's emotion detection passes emotion state correctly to TTS.

**Script:**
```python
# Set test audio file
export TEST_EMOTION_AUDIO="path/to/test_emotion_clip.wav"
python sonora/scripts/run_tests.py --test 5
```

**Or Python API:**
```python
import requests

# Upload a short emotional voice sample
files = {"file": open("test_emotion_clip.wav", "rb")}
response = requests.post("http://127.0.0.1:8000/api/emotion/detect", files=files)
emotion = response.json().get("emotion")

# Pass detected emotion to Coqui
tts_payload = {
    "text": "Emotion detected and reflected.",
    "emotion": emotion,
    "provider": "coqui"
}
tts_response = requests.post("http://127.0.0.1:8000/api/tts/generate", json=tts_payload)
with open(f"emotion_{emotion}.wav", "wb") as f:
    f.write(tts_response.content)
```

**Expected Output:**
- Emotion detected correctly (`sad`, `angry`, `happy`, etc.)
- Generated audio reflects that emotion
- Confidence score > 0.5

**✅ Pass Criteria:**
- Emotion transfer pipeline working end-to-end
- Emotion detected with reasonable confidence
- TTS reflects detected emotion

**❌ Failure Indicators:**
- Emotion detection fails
- Low confidence scores
- TTS doesn't reflect emotion

**Debug Steps:**
- Check SpeechBrain model download
- Verify audio file format (WAV, 16kHz recommended)
- Check emotion classifier initialization

---

### TEST 6 — End-to-End Dubbing Flow

**Goal:** Verify Whisper ASR → Translation → Emotion Detection → TTS → Lip-Sync pipeline works.

**Script:**
```python
# Set test audio/video file
export TEST_DUBBING_AUDIO="path/to/sample_anime_clip.wav"
python sonora/scripts/run_tests.py --test 6
```

**Or Python API:**
```python
import requests

files = {"file": open("sample_anime_clip.wav", "rb")}
response = requests.post("http://127.0.0.1:8000/api/dub", files=files)
with open("dubbed_output.wav", "wb") as f:
    f.write(response.content)
```

**Expected Result:**
- Output audio file with synchronized speech
- English dub (if Japanese input)
- Emotion preserved
- Duration mismatch < 0.5s

**✅ Pass Criteria:**
- End-to-end functional confirmation
- Output file generated
- Audio quality acceptable

**❌ Failure Indicators:**
- Pipeline fails at any stage
- Output file missing or corrupted
- Lip desync (if video processing)

**Debug Steps:**
- Check each pipeline stage logs
- Verify Whisper ASR model
- Check Wav2Lip / SadTalker model load paths (if using video)

---

## 📈 Benchmark Suite

### TEST 7 — Efficiency Benchmark

**Goal:** Measure model performance across providers.

**Command:**
```bash
python sonora/scripts/benchmark_tts_translation.py
```

**Metrics Logged:**

| Provider     | Avg Latency (s) | Output Quality | Emotion Accuracy |
|--------------|----------------|---------------|------------------|
| Hugging Face | < 1.2          | Fluent        | High             |
| Coqui        | < 4.0          | Natural       | 85–90%           |
| VibeVoice    | < 3.0          | Smooth        | 90%              |
| Whisper ASR  | < 2.5          | Accurate      | —                |

**Output:**
- CSV file saved to `logs/benchmark_YYYYMMDD_HHMMSS.csv`
- Summary table printed to console

---

## 🐞 Debugging Guide

### If UI Fails

If the **UI window ("=== SONORA UI ===")** doesn't start:

1. **Open PowerShell window**
2. **Check error logs:**
   ```powershell
   streamlit run ui/main.py
   ```
3. **Common causes:**
   - Port 8501 already in use → change to 8502
   - Missing import (`coqui_tts`, `local_translator`) → run `pip install -r sonora/requirements.txt`
   - Torch not found → reinstall: `pip install torch torchvision torchaudio`

4. **Relaunch:**
   ```bash
   streamlit run sonora/ui/main.py --server.port 8501
   ```

### API Connection Issues

**Check if API is running:**
```bash
curl http://127.0.0.1:8000/health
```

**Check port:**
```powershell
netstat -ano | findstr ":8000"
```

**Kill process on port (if needed):**
```powershell
$process = Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force
```

### Model Loading Issues

**Check model downloads:**
- Translation: `~/.cache/huggingface/transformers/`
- Coqui TTS: `~/.local/share/tts/`
- SpeechBrain: `~/.cache/speechbrain/`

**Force re-download:**
```python
# Clear cache and re-download
from transformers import pipeline
pipeline("translation", model="Helsinki-NLP/opus-mt-ja-en", force_download=True)
```

---

## ✅ Expected Outcomes Summary

| Test | Target            | Expected Result               | Pass Criteria                  |
|------|-------------------|-------------------------------|--------------------------------|
| 1    | API Health        | `{"status":"ok"}`             | All components initialized     |
| 2    | Translation       | Fast & accurate output         | < 6s cold, < 1s warm           |
| 3    | Coqui TTS         | Natural, emotion-controlled    | < 4s CPU, playable audio       |
| 4    | VibeVoice         | Functional, consistent timing  | < 3s, quality audio            |
| 5    | Emotion Detection | Correct mapping                | Emotion detected, TTS reflects  |
| 6    | Full Dubbing      | Synced dubbed output           | Pipeline completes successfully|
| 7    | Benchmark         | Efficiency metrics logged      | CSV file generated             |

---

## 📝 Notes

- All tests are designed to run offline (no external API calls)
- Tests can be run individually or as a suite
- Benchmark results are saved to CSV for analysis
- Test audio files can be provided via environment variables

---

## 🔗 Related Files

- `sonora/tests/test_sonora_integration.py` - Main test suite
- `sonora/scripts/benchmark_tts_translation.py` - Benchmark script
- `sonora/scripts/run_tests.py` - Test runner
- `sonora/api/server.py` - API server
- `sonora/api/routes_*.py` - API route handlers

---

**Last Updated:** 2024
**Version:** 1.0.0













