# -*- coding: utf-8 -*-
import os
import shutil
import logging
import time
from typing import List, Optional
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from gradio_client import Client, handle_file
from sonora.audio_editing.path_manager import get_data_dir
from src.core.reliability import get_available_memory

logger = logging.getLogger("sonora.shadow_providers")

def cloud_separate_audio(input_audio_path: str) -> str:
    """Compatibility wrapper — returns just the vocals path from the full 5-stem pipeline."""
    stems = cloud_granular_separation(input_audio_path)
    return stems.get("vocals", input_audio_path)

def _apply_refinement_pass(y: "np.ndarray", sr: int, target_lufs: float = -14.0) -> "np.ndarray":
    """
    Audio Surgery 2.1 Refinement Pass:
    1. EBU R128 loudness normalization to target LUFS.
    2. 50ms micro-fades on segment boundaries (anti-pop).
    Returns the processed audio array.
    """
    import numpy as np
    if y is None or len(y) == 0:
        return y

    # ---- 1. EBU R128 Normalization (simple RMS-based loudness normalization) ----
    rms = np.sqrt(np.mean(y ** 2))
    if rms > 1e-9:
        # Target -0.1 dBTP ≈ 0.989 max amplitude; normalize by RMS first
        target_rms = 10 ** (target_lufs / 20.0)
        y = y * (target_rms / rms)
        # Hard-clip to -0.1 dBTP true peak
        peak_limit = 10 ** (-0.1 / 20.0)
        y = np.clip(y, -peak_limit, peak_limit)

    # ---- 2. 50ms Micro-Fades (Anti-Pop) ----
    fade_samples = int(sr * 0.050)  # 50ms
    if len(y) > fade_samples * 2:
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        if y.ndim == 1:
            y[:fade_samples] *= fade_in
            y[-fade_samples:] *= fade_out
        else:
            y[:, :fade_samples] *= fade_in
            y[:, -fade_samples:] *= fade_out

    return y


def _extract_emotional_cues(vocals: "np.ndarray", sr: int, word_timestamps: list) -> tuple:
    """
    Audio Surgery 2.1 — Broad Universal Cue Detector.
    Separates pure speech segments from non-verbal emotional cues (laughs, gasps, shouts).

    Strategy:
    - Subtract word-aligned segments from the vocal track → remaining audio = cues.
    - No minimum duration restriction — any non-silent non-word audio is a cue.
    - Spectral gate on vocal range [300Hz – 8kHz] to catch human non-verbal sounds.

    Returns: (vocal_chat, emotional_cues) as numpy arrays.
    """
    import numpy as np
    try:
        import librosa
    except ImportError:
        # If librosa not available, return vocals as chat and silence as cues
        return vocals, np.zeros_like(vocals)

    # Start with silence for both outputs
    chat = np.zeros_like(vocals)
    cues = vocals.copy()  # Everything starts as cues; words are moved to chat

    if word_timestamps:
        for word in word_timestamps:
            start_s = word.get("start", 0)
            end_s = word.get("end", start_s + 0.3)
            # Add small context window around each word
            start_sample = max(0, int((start_s - 0.05) * sr))
            end_sample = min(len(vocals), int((end_s + 0.05) * sr))
            chat[start_sample:end_sample] = vocals[start_sample:end_sample]
            cues[start_sample:end_sample] = 0.0  # Remove speech from cues

    # ---- Spectral Gate on Cues: keep only human vocal range [300Hz – 8kHz] ----
    # This filters out pure instrumental bleed from the cues track
    try:
        D = librosa.stft(cues)
        freqs = librosa.fft_frequencies(sr=sr)
        # Build a frequency mask for vocal range
        vocal_mask = (freqs >= 300) & (freqs <= 8000)
        # Zero out energy outside vocal range in the cues spectrogram
        D_filtered = D.copy()
        D_filtered[~vocal_mask, :] = 0
        # Apply silence floor (-45 dBFS ≈ 0.006 amplitude)
        amplitude = np.abs(D_filtered)
        silence_floor = 10 ** (-45.0 / 20.0)
        D_filtered[amplitude < silence_floor] = 0
        cues = librosa.istft(D_filtered, length=len(cues))
    except Exception as e:
        logger.warning(f"Spectral gating failed, using raw cues: {e}")

    return chat, cues


def cloud_granular_separation(input_audio_path: str, word_timestamps: list = None) -> dict:
    """
    Audio Surgery 2.1 — Master Class Granular 4-Stem Cloud Isolation.

    Pipeline:
    1. htdemucs_ft (Fine-Tuned) splits audio into: vocals, bass, drums, other.
    2. HPSS on 'other' → background_songs (harmonic) vs music_percussive.
    3. Spectral Subtraction on 'vocals' → vocal_chat (speech) + emotional_cues (non-verbal).
    4. Micro-Fades + EBU R128 normalization on every stem.

    Produces 5 stems: vocals, music, chat, cues, songs.
    """
    import numpy as np
    try:
        import soundfile as sf
        import librosa
    except ImportError as e:
        raise RuntimeError(f"Required audio library missing: {e}. Install soundfile and librosa.")

    logger.info(f"🚀 [SURGERY 2.1] Starting Master Class 4-Stem Separation for {input_audio_path}")

    # ── STEP 1: Cloud Demucs via HF Spaces (htdemucs_ft preferred) ──────────────
    spaces_config = [
        ("facebook/demucs", "htdemucs_ft"),
        ("afrideva/demucs", "htdemucs"),
        ("facebook/demucs", "htdemucs"),
    ]
    hf_token = os.getenv("HF_TOKEN")
    vocals_temp = drums_temp = bass_temp = other_temp = None

    def _attempt_space(space, model):
        try:
            logger.info(f"🔗 Neural Handshake → {space} [{model}]...")
            client = Client(space, hf_token=hf_token)
            logger.info(f"⚡ Neural Link Active → {space} [{model}]. Processing...")
            result = client.predict(
                audio=handle_file(input_audio_path),
                model=model,
                api_name="/predict"
            )
            return result, space, model
        except Exception as e:
            logger.warning(f"⚠️ {space} [{model}] failed: {e}")
            return None

    # Parallel Burst Handshake (Take the first success)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(_attempt_space, s, m) for s, m in spaces_config]
        for future in as_completed(futures):
            res = future.result()
            if res:
                result, space, model = res
                logger.info(f"✅ Fast-Path Success via {space} [{model}]")
                
                # Handle different return formats from Gradio
                if isinstance(result, (list, tuple)) and len(result) >= 4:
                    vocals_temp, bass_temp, drums_temp, other_temp = result[0], result[1], result[2], result[3]
                elif isinstance(result, str) and os.path.exists(result):
                    if os.path.isdir(result):
                        files = os.listdir(result); 
                        for f in files:
                            full_p = os.path.join(result, f)
                            if "vocals" in f.lower(): vocals_temp = full_p
                            if "bass" in f.lower(): bass_temp = full_p
                            if "drums" in f.lower(): drums_temp = full_p
                            if "other" in f.lower() or "no_vocals" in f.lower(): other_temp = full_p
                    else: vocals_temp = result; other_temp = result
                
                # If we found at least vocals and other, we are done
                if vocals_temp and other_temp:
                    break

    if not vocals_temp:
        logger.error(
            "❌ ALL Cloud Separation attempts failed (htdemucs_ft, htdemucs). "
            f"HF_TOKEN {'is set' if hf_token else 'is MISSING'}. "
            "Ensure HF_TOKEN is in .env and HuggingFace Spaces are online. Falling back to original audio."
        )
        return {"vocals": input_audio_path, "music": input_audio_path, "chat": input_audio_path, "cues": input_audio_path, "songs": input_audio_path}


    # ── STEP 2: Load stems into numpy ──────────────────────────────────────────
    def _load(path):
        if path and os.path.exists(path):
            try:
                y, sr = sf.read(path, always_2d=False)
                if y is None: return None, None
                # Convert stereo to mono for processing
                return (y[:, 0] + y[:, 1]) / 2 if y.ndim == 2 else y, sr
            except Exception as e:
                logger.error(f"Failed to load stem {path}: {e}")
                return None, None
        return None, None

    y_vocals, sr = _load(vocals_temp)
    y_other, _ = _load(other_temp)
    y_bass, _ = _load(bass_temp)
    y_drums, _ = _load(drums_temp)

    if y_vocals is None:
        raise RuntimeError("Vocals stem could not be loaded after separation.")

    # ── STEP 3: HPSS on 'other' → Songs (harmonic singing) vs Music (percussive) ──
    logger.info("🎵 [HPSS] Separating harmonic singing from instrumental music...")
    try:
        if y_other is not None:
            # Memory Guard: HPSS is expensive. Need ~1.5GB for 5 min audio.
            avail_gb = get_available_memory()
            duration_m = len(y_other) / (sr * 60)
            mem_needed = duration_m * 0.3 # Rough estimate: 0.3GB per minute
            
            if avail_gb < mem_needed:
                logger.warning(f"⚠️ [MEMORY GUARD] Low memory ({avail_gb:.1f}GB avail). Skipping HPSS to prevent crash.")
                y_songs = np.zeros_like(y_other)
                y_music = y_other
            else:
                D_other = librosa.stft(y_other)
                D_harmonic, D_percussive = librosa.decompose.hpss(D_other, margin=3.0)
                y_songs = librosa.istft(D_harmonic, length=len(y_other))   # Singing / Opera
                y_music = librosa.istft(D_percussive, length=len(y_other)) # Instruments

            # Merge bass and drums into the music bed if available
            if y_bass is not None:
                min_len = min(len(y_music), len(y_bass))
                y_music[:min_len] += y_bass[:min_len] * 0.8
            if y_drums is not None:
                min_len = min(len(y_music), len(y_drums))
                y_music[:min_len] += y_drums[:min_len] * 0.9
        else:
            y_songs = np.zeros_like(y_vocals)
            y_music = np.zeros_like(y_vocals)
    except Exception as e:
        logger.warning(f"HPSS failed, falling back to raw stems: {e}")
        y_songs = y_other if y_other is not None else np.zeros_like(y_vocals)
        y_music = y_other if y_other is not None else np.zeros_like(y_vocals)

    # ── STEP 4: Neural Subtraction → Vocal Chat + Emotional Cues ────────────────
    logger.info("🗣️ [NEURAL SUBTRACTION] Extracting emotional cues from vocal track...")
    try:
        y_chat, y_cues = _extract_emotional_cues(y_vocals, sr, word_timestamps or [])
    except Exception as e:
        logger.warning(f"Cue extraction failed, using raw vocal: {e}")
        y_chat = y_vocals
        y_cues = np.zeros_like(y_vocals)

    # ── STEP 5: Refinement Pass — Micro-Fades + Normalization ───────────────────
    logger.info("✨ [REFINEMENT] Applying micro-fades and EBU R128 normalization...")
    y_vocals = _apply_refinement_pass(y_vocals, sr)
    y_chat   = _apply_refinement_pass(y_chat,   sr)
    y_cues   = _apply_refinement_pass(y_cues,   sr)
    y_songs  = _apply_refinement_pass(y_songs,  sr)
    y_music  = _apply_refinement_pass(y_music,  sr)

    # ── STEP 6: Save all stems to shared volume ──────────────────────────────────
    # [PATH ALIGNMENT] Use get_data_dir() instead of /tmp/sonora for local consistency
    output_dir = os.path.join(
        get_data_dir(),
        "stems",
        os.path.basename(input_audio_path).replace(".", "_")
    )
    os.makedirs(output_dir, exist_ok=True)

    def _save(y, path, sample_rate):
        try:
            sf.write(path, y.astype(np.float32), sample_rate)
        except Exception as e:
            logger.error(f"Failed to save stem {path}: {e}")

    _save(y_vocals, paths["vocals"], sr)
    _save(y_music,  paths["music"],  sr)
    _save(y_chat,   paths["chat"],   sr)
    _save(y_cues,   paths["cues"],   sr)
    _save(y_songs,  paths["songs"],  sr)

    logger.info(f"✅ [SURGERY 2.1] All 5 stems saved to {output_dir}")
    return paths


def _ensure_mp3(audio_path: str) -> str:
    """Uses ffmpeg to extract a high-quality mono MP3 from any media file, with caching."""
    import ffmpeg
    import os
    import hashlib
    from sonora.audio_editing.path_manager import get_data_dir
    
    shared_dir = str(get_data_dir())
    os.makedirs(shared_dir, exist_ok=True)
    
    # Generate unique hash for this audio path to avoid redundant conversions
    path_hash = hashlib.md5(audio_path.encode()).hexdigest()[:8]
    out_path = os.path.join(shared_dir, f"transcribe_{path_hash}.mp3")
    
    # Cache Check: If exists and non-empty, skip
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        logger.info(f"✨ [CACHE] Using existing high-quality MP3 for ASR: {out_path}")
        return out_path
        
    try:
        logger.info(f"FFmpeg: Extracting portable MP3 from {audio_path}...")
        # Ensure target directory exists for the conversion output
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        (
            ffmpeg.input(audio_path)
            .output(out_path, ac=1, ar='16k', audio_bitrate='128k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return out_path
    except Exception as e:
        stderr = getattr(e, 'stderr', b'').decode() if hasattr(e, 'stderr') else str(e)
        logger.error(f"FFmpeg MP3 extraction failed for {audio_path}: {stderr}")
        # If extraction failed, return original but it might fail later in Groq/OpenAI
        return audio_path

def cloud_run_transcription(audio_path: str) -> list:
    """
    Cloud ASR Node: Routes to Groq (Fastest) with robust fallbacks to Gemini and OpenAI.
    """
    clean_audio_path = _ensure_mp3(audio_path)
    
    # --- PROVIDER 1: Groq (Whisper Large-v3) ---
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            logger.info(f"⚡ Neural Link: Offloading ASR to Groq (MP3: {os.path.basename(clean_audio_path)})...")
            from groq import Groq
            client = Groq(api_key=groq_key)
            with open(clean_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=("audio.mp3", audio_file, "audio/mpeg"),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                )
                
                result = transcription.model_dump()
                words_list = []
                if "words" in result and result["words"]:
                    words_list = result["words"]
                elif "segments" in result and result["segments"]:
                    for seg in result["segments"]:
                        if "words" in seg:
                            words_list.extend(seg["words"])
                
                if not words_list:
                    words_list = result.get("segments", [])
                
                for w in words_list:
                    if 'word' not in w and 'text' in w: w['word'] = w['text']
                
                return words_list
        except Exception as e:
            logger.error(f"❌ [NEURAL LINK] Groq ASR failed: {e}. Falling back to Gemini...")

    # --- PROVIDER 2: Gemini 1.5 Flash (Native Audio ASR) ---
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            logger.info("⚡ Neural Link: Offloading ASR to Gemini 1.5 Flash (Long-File Resilience)...")
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            
            # Gemini 1.5 Flash handles audio natively without word-level timestamps sometimes, 
            # so we use a specialized prompt to get time-coded words if possible.
            audio_file = genai.upload_file(path=clean_audio_path)
            prompt = (
                "You are a verbatim transcriber for anime dubbing. "
                "Transcribe the audio and output ONLY a JSON list of word objects. "
                "CRITICAL: Each sentence MUST be broken into individual word objects. "
                "Format: [{'word': 'Word.', 'start': 0.0, 'end': 0.5}, ...]"
            )
            response = model.generate_content([prompt, audio_file])
            
            # Simple JSON extraction from markdown if needed
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
            
            import json
            words_list = json.loads(text)
            logger.info("✅ [SUCCESS] Gemini 1.5 Flash Word-Level extraction complete.")
            return words_list
        except Exception as e:
            logger.error(f"❌ [NEURAL LINK] Gemini ASR failed: {e}. Falling back to OpenAI...")

    # --- PROVIDER 3: OpenAI Whisper-1 ---
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(clean_audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.mp3", audio_file, "audio/mpeg"),
                    response_format="verbose_json"
                )
                result = response.model_dump()
                words_list = []
                if "words" in result and result["words"]:
                    words_list = result["words"]
                elif "segments" in result and result["segments"]:
                    for seg in result["segments"]:
                        if "words" in seg: words_list.extend(seg["words"])
                
                if not words_list: words_list = result.get("segments", [])
                for w in words_list:
                    if 'word' not in w and 'text' in w: w['word'] = w['text']
                
                return words_list
        except Exception as e:
            logger.error(f"❌ [NEURAL LINK] OpenAI ASR fallback failed: {e}")
            
    return []

def cloud_translate_segment(japanese_text: str, target_syllables: int, style: str) -> str:
    """Fallback: GPT-4o Isometric Translation (Legacy)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return f"[ERROR] No OpenAI KEY for Fallback"
    client = OpenAI(api_key=api_key)
    prompt = f"Translate to English in {style} style. Target syllables: {target_syllables}. Text: {japanese_text}"
    completion = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return completion.choices[0].message.content.strip()

def cloud_generate_voice(text: str, voice_id: str) -> bytes:
    """Fallback: ElevenLabs synthesis."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key: raise RuntimeError("ElevenLabs API Key missing")
    client = ElevenLabs(api_key=api_key)
    audio_gen = client.text_to_speech.convert(voice_id=voice_id, text=text, model_id="eleven_flash_v2_5")
    return b"".join(list(audio_gen))
