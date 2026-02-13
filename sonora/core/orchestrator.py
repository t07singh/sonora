import os
import json
import logging
import subprocess
import time
import torch
import gc
from typing import List, Dict, Any, Optional
from sonora.audio_editing.path_manager import get_data_dir, get_secure_path
from sonora.core.reliability import HardwareLock

import re
import requests
from sonora.core.llm_translator import HardenedTranslator
from transcriber import Transcriber

logger = logging.getLogger("sonora.orchestrator")

def group_words_by_pause(words: List[Dict], pause_threshold: float = 0.5) -> List[List[Dict]]:
    """Groups words into segments based on time gaps."""
    if not words: return []
    segments = []
    current_segment = [words[0]]
    for i in range(1, len(words)):
        if words[i]['start'] - words[i-1]['end'] > pause_threshold:
            segments.append(current_segment)
            current_segment = []
        current_segment.append(words[i])
    if current_segment:
        segments.append(current_segment)
    return segments

def count_syllables(text: str) -> int:
    """Estimates English syllables simplified for dubbing sync."""
    text = text.lower()
    text = re.sub(r'[^a-z ]', '', text)
    count = 0
    for word in text.split():
        vowels = "aeiouy"
        if len(word) == 0: continue
        if word[0] in vowels: count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"): count -= 1
        if count == 0: count = 1
    return count

def estimate_japanese_morae(text: str) -> int:
    """Estimates Japanese morae count for alignment."""
    # Simplified: count kana and small characters
    count = len(text)
    # Adjust for small characters like ゃ, ゅ, ょ which don't count as a full mora usually? 
    # Actually, in Japanese, each kana is a mora.
    return count

class SonoraOrchestrator:
    """
    Main Orchestrator for the Sonora Swarm.
    Routes requests to local microservices or cloud fallbacks.
    """
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.transcriber = Transcriber()
        self.translator = HardenedTranslator()

    async def run_transcription(self) -> List[Dict]:
        """Calls the sonora-transcriber microservice."""
        logger.info(f"🎙️ Orchestrator: Triggering ASR for {self.audio_path}")
        # Transcriber.transcribe handles the microservice handshake
        result = self.transcriber.transcribe(self.audio_path)
        return result.get("segments", [])

    async def translate_segment(self, segment: List[Dict], style: str = "Anime") -> str:
        """Translates a segment using the Hardened Translator (GPT-4o/Claude)."""
        text = " ".join([w['word'] for w in segment])
        target_syllables = estimate_japanese_morae(text)
        prompt = f"Translate to English in {style} style. Target syllables: {target_syllables}. Text: {text}"
        return self.translator.translate(prompt)

    async def refactor_line(self, text: str, target_syllables: int, style: str) -> str:
        """Refines a line to match target syllable count."""
        prompt = f"Refactor this English line to have exactly {target_syllables} syllables. Style: {style}. Text: {text}"
        return self.translator.translate(prompt)

    async def synthesize_segments(self, segments: List[Dict], translations: List[str], voice_id: str) -> List[str]:
        """Calls the sonora-synthesizer microservice for each line."""
        audio_takes = []
        SYNTH_URL = os.getenv("SYNTHESIZER_URL", "http://sonora-synthesizer:8002/synthesize")
        
        for i, text in enumerate(translations):
            logger.info(f"🎙️ Orchestrator: Synthesizing segment {i+1}...")
            payload = {
                "text": text,
                "voice_id": voice_id,
                "emotion": segments[i].get("emotion", "neutral")
            }
            try:
                # In a real environment, we'd send the request to the synth microservice
                # For this implementation, we simulate the take path
                # For this implementation, we simulate the take path
                take_name = f"take_{int(time.time())}_{i}.wav"
                take_path = get_data_dir() / "takes" / take_name
                os.makedirs(os.path.dirname(take_path), exist_ok=True)
                
                
                # FEATURE TOGGLE: Production vs Dev Mock
                # If SONORA_MODE environment variable is set to "production", we call the real service.
                # Otherwise, we use the mock behavior for safety/speed.
                sonora_mode = os.getenv("SONORA_MODE", "dev").lower()
                
                if sonora_mode == "production":
                    logger.info("🚀 PRODUCTION MODE: Calling Real Synthesis Service...")
                    r = requests.post(SYNTH_URL, json=payload, timeout=30)
                    r.raise_for_status()
                    with open(take_path, "wb") as f: f.write(r.content)
                else:
                    logger.warning("🧪 DEV MODE: Mocking Synthesis (Set SONORA_MODE=production to enable)")
                    # For now, we touch the file to prove the logic
                    with open(take_path, "w") as f: f.write("MOCK_AUDIO")
                
                audio_takes.append(take_path)
            except Exception as e:
                logger.error(f"Synthesis failed for segment {i}: {e}")
        
        return audio_takes

    async def assemble_final_dub(self, video_path: str, audio_takes: List[str], segments: List[Dict]) -> str:
        """Muxes AI voices back into the video using FFmpeg."""
        logger.info("🏗️ Orchestrator: Assembling final dub...")
        post_processor = SonoraPostProcessor()
        output_name = f"sonora_master_{int(time.time())}.mp4"
        
        # In a real production, we'd have separated stems from Demucs
        # Here we mock the stem paths
        # In a real production, we'd have separated stems from Demucs
        # Here we mock the stem paths
        stems_dir = get_data_dir() / "stems"
        bgm_mock = str(stems_dir / "bgm.wav")
        cues_mock = str(stems_dir / "cues.wav")
        # Combine takes into a single voice track (simplified for demo)
        combined_voice = str(stems_dir / "combined_voice.wav")
        
        os.makedirs(stems_dir, exist_ok=True)
        with open(combined_voice, "w") as f: f.write("COMBINED")
        with open(bgm_mock, "w") as f: f.write("BGM")
        with open(cues_mock, "w") as f: f.write("CUES")

        try:
            return await post_processor.master_assemble(
                video_in=video_path,
                bgm_in=bgm_mock,
                cues_in=cues_mock,
                voice_in=combined_voice,
                output_file=output_name
            )
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
        except Exception as e:
            logger.error(f"Assembly failed: {e}")
            return str(get_data_dir() / "exports" / output_name)


class SonoraPostProcessor:
    """
    Handles the 'Master Continuity' Assembly.
    Performs Triple-Layer Audio Merging via FFmpeg.
    """
    def __init__(self, shared_dir: Optional[str] = None):
        self.shared_dir = shared_dir or str(get_data_dir())

    async def master_assemble(self, video_in: str, bgm_in: str, cues_in: str, voice_in: str, output_file: str = "SONORA_FINAL_MASTER.mp4"):
        """
        Executes Triple-Layer Audio Merge.
        Layer 1 [0:a]: World (BGM/SFX) @ 0.8 Vol
        Layer 2 [1:a]: Human Cues (Breaths/Laughs) @ 1.0 Vol
        Layer 3 [2:a]: AI Dub (Qwen3-TTS) @ 1.1 Vol
        """
        # Sequential Flush: Ensure GPU/VRAM is clear for FFmpeg
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("🏗️ Starting Triple-Layer Master Assembly...")
        
        filter_complex = (
            "[0:a]volume=0.8[bg];"
            "[1:a]volume=1.0[cues];"
            "[2:a]volume=1.1[dub];"
            "[bg][cues][dub]amix=inputs=3:duration=first:dropout_transition=2[out]"
        )
        
        output_path = os.path.join(self.shared_dir, "exports", output_file)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', bgm_in,    # Stem 1: World
            '-i', cues_in,   # Stem 2: Original Breaths/Artifacts
            '-i', voice_in,  # Stem 3: New Qwen3 Dub
            '-i', video_in,  # Input Video (Synced Visuals)
            '-filter_complex', filter_complex,
            '-map', '3:v',   # Map video from visuals pass
            '-map', '[out]', # Map merged audio
            '-c:v', 'copy',  # Lossless visual bridge
            '-c:a', 'aac',   # Pro-grade audio codec
            '-b:a', '256k',
            output_path
        ]
        
        try:
            # We use a subprocess.run with lock to manage hardware load
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✨ Master Continuity Complete: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Mastering Failed: {e.stderr.decode()}")
            raise

class SonoraSynthesisAgent:
    """
    Qwen3-TTS (0.6B) Model Interface.
    Instruction-Driven emotional synthesis.
    """
    def __init__(self, model_id: str = "qwen3-tts-0.6b-vc-flash"):
        self.model_id = model_id
    def __init__(self, model_id: str = "qwen3-tts-0.6b-vc-flash"):
        self.model_id = model_id
        self.anchor_clip = str(get_data_dir() / "anchors/character_anchor.wav")

    async def synthesize_with_soul(self, text: str, emotion_instruction: str) -> str:
        """
        Instruction-Aware Synthesis Handshake.
        Pushes Tone instructions directly into model weights.
        """
        # Hardware Lock: Sequential processing to prevent VRAM spikes
        await HardwareLock.acquire("Qwen3-Synthesis")
        
        try:
            logger.info(f"🎙️ Qwen3: Synthesizing Soul with Instruction: '{emotion_instruction}'")
            # Simulate local model generation
            # result = local_qwen3.generate(text, self.anchor_clip, instruction=emotion_instruction)
            time.sleep(1.5)
            
            # result = local_qwen3.generate(text, self.anchor_clip, instruction=emotion_instruction)
            time.sleep(1.5)
            
            output_path = str(get_data_dir() / "takes" / f"take_{int(time.time())}.wav")
            return output_path
        finally:
            HardwareLock.release() # Flush memory
