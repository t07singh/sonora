# 🧪 Sonora Test Suite - Quick Reference

## ✅ What's Been Created

### 1. **New API Endpoints**
- ✅ `/api/translate` - Offline Hugging Face translation
- ✅ `/api/emotion/detect` - SpeechBrain emotion detection
- ✅ `/api/tts/generate` - TTS generation (Coqui/VibeVoice) - Already existed

### 2. **Test Scripts**
- ✅ `sonora/tests/test_sonora_integration.py` - Comprehensive test suite (Tests 1-6)
- ✅ `sonora/scripts/benchmark_tts_translation.py` - Efficiency benchmark (Test 7)
- ✅ `sonora/scripts/run_tests.py` - Test runner with CLI options

### 3. **Documentation**
- ✅ `sonora/TEST_PLAN.md` - Complete test plan documentation

### 4. **Server Updates**
- ✅ Updated `sonora/api/server.py` to include new routes
- ✅ Enhanced `/health` endpoint with more details

---

## 🚀 Quick Start

### Start the API Server
```bash
cd sonora
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

### Run All Tests
```bash
python sonora/scripts/run_tests.py
```

### Run Specific Test
```bash
python sonora/scripts/run_tests.py --test 1  # API Health
python sonora/scripts/run_tests.py --test 2  # Translation
python sonora/scripts/run_tests.py --test 3  # Coqui TTS
python sonora/scripts/run_tests.py --test 4  # VibeVoice
python sonora/scripts/run_tests.py --test 5  # Emotion Detection
python sonora/scripts/run_tests.py --test 6  # End-to-End Dubbing
```

### Run Benchmark
```bash
python sonora/scripts/benchmark_tts_translation.py
```

---

## 📋 Test Overview

| # | Test Name | Endpoint | Status |
|---|-----------|----------|--------|
| 1 | API Health | `GET /health` | ✅ Ready |
| 2 | Translation | `POST /api/translate` | ✅ Ready |
| 3 | Coqui TTS | `POST /api/tts/generate` | ✅ Ready |
| 4 | VibeVoice | `POST /api/tts/generate` | ✅ Ready |
| 5 | Emotion Detection | `POST /api/emotion/detect` | ✅ Ready |
| 6 | End-to-End Dubbing | `POST /api/dub` | ✅ Ready |
| 7 | Benchmark | N/A (Script) | ✅ Ready |

---

## 🔧 Configuration

### Environment Variables

```bash
# API URL (default: http://127.0.0.1:8000)
export SONORA_API_URL="http://127.0.0.1:8000"

# Test audio files (optional)
export TEST_EMOTION_AUDIO="path/to/emotion_clip.wav"
export TEST_DUBBING_AUDIO="path/to/anime_clip.wav"
export TEST_ASR_AUDIO="path/to/asr_test.wav"
```

---

## 📊 Expected Results

### Test 1: API Health
- ✅ Status: `"ok"`
- ✅ All components initialized
- ✅ Uptime reported

### Test 2: Translation
- ✅ Cold start: < 6s
- ✅ Warm inference: < 1s
- ✅ Accurate translation

### Test 3: Coqui TTS
- ✅ Generation: < 4s (CPU), < 2s (GPU)
- ✅ Playable audio file
- ✅ Emotion affects voice

### Test 4: VibeVoice
- ✅ Generation: < 3s
- ✅ Quality audio
- ✅ Consistent timing

### Test 5: Emotion Detection
- ✅ Emotion detected with confidence > 0.5
- ✅ TTS reflects detected emotion

### Test 6: End-to-End Dubbing
- ✅ Full pipeline completes
- ✅ Output file generated
- ✅ Duration mismatch < 0.5s

### Test 7: Benchmark
- ✅ CSV file generated in `logs/`
- ✅ Summary table printed

---

## 🐞 Troubleshooting

### API Not Responding
```bash
# Check if server is running
curl http://127.0.0.1:8000/health

# Check port
netstat -ano | findstr ":8000"
```

### Import Errors
```bash
# Install dependencies
pip install -r sonora/requirements.txt
```

### Model Loading Issues
- Translation: Check `~/.cache/huggingface/transformers/`
- Coqui TTS: Check `~/.local/share/tts/`
- SpeechBrain: Check `~/.cache/speechbrain/`

---

## 📝 Notes

- All tests are designed to run **offline** (no external API calls)
- Tests can be run individually or as a suite
- Benchmark results saved to CSV in `logs/` directory
- Optional test audio files can be provided via environment variables

---

## 📚 Full Documentation

See `sonora/TEST_PLAN.md` for complete documentation including:
- Detailed test descriptions
- Debugging guides
- Expected outcomes
- API endpoint details

---

**Created:** 2024
**Version:** 1.0.0













