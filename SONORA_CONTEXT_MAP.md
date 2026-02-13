# SONORA SWARM: SYSTEM CONTEXT MAP (v1.0)

## 🏗️ Architecture Overview
- **Orchestrator:** Python-based logic hub (`sonora/core/orchestrator.py`).
- **Worker Swarm:** Stateless containers for TTS/STT.
- **State Management:** Local file-polling via `shared_data` (Host) mapped to `/tmp/sonora` (Container).
- **Qwen3 Service:** Standalone FastAPI service in `src/providers/qwen3/qwen3_service.py` (Mocked/Placeholder).

## 📂 Logic Manifest
### `sonora/core/orchestrator.py`
- **Role:** Central coordination of transcription, translation, and synthesis.
- **Logic:** `Input -> Whisper (API) -> Surgical Translation (GPT-4o) -> Route to Provider (Qwen3/Vibe) -> Post-Process (StepAudio/Spectral)`.
### `src/providers/qwen3/qwen3_service.py`
- *Current Status:* Placeholder / Mock.
- *Goal:* Integrate Qwen3-TTS as a high-fidelity local alternative.
- *Mechanism:* Polls `/tmp/sonora/tasks` for JSON, generates audio, writes to `shared_data/outputs`.

## 🔴 Current Constraints (IMPORTANT)
- **Environment:** WSL2 / Ubuntu.
- **Hardware:** CPU-Hardened (Minimal GPU usage to avoid driver crashes).
- **Pathing Issue:** Orchestrator writes to `/tmp/sonora` (Container Path) which may not align with Host `shared_data` unless fixed.
- **Latency:** File polling introduces minimum latency (0.5s poll interval).

## 🛡️ Resilience Strategy: Retry-with-Fallback
- **Primary:** Qwen3-TTS (Target Latency: <5s).
- **Secondary (Fallback):** VibeVoice (Legacy stable).
- **Trigger:** Any Qwen3 task taking >5000ms is abandoned.

### 🔄 The Atomic Handshake 
To prevent "Ghost Audio" (late writes from timed-out services):
1. Orchestrator writes `task_123.json`.
2. If `output_123.wav` doesn't appear in 5s, Orchestrator deletes `task_123.json`.
3. Orchestrator re-issues `task_123_fallback.json` (internally handled via VibeVoice call).

## 🧠 Logic Summaries

### Orchestrator Logic (Implemented)
```python
def process_pipeline(input_audio, text):
    # 1. Analyze Emotion & Cues
    cues = tokenizer.analyze(input_audio)
    
    # 2. Try Qwen3 (Fast, Local) with Fallback
    audio = dispatch_to_qwen(text, timeout=5.0)
    
    if not audio:
        # 3. Fallback to VibeVoice
        print("[Orchestrator] Qwen3 Timeout. Initiating VibeVoice Fallback.")
        audio = vibe_voice.perform_transfer(text, cues)
        
    # 4. Post-Process (Spectral & Splicing)
    audio = refiner.spectral_match(audio, input_audio)
    return audio
```
