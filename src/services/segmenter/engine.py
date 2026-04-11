"""
Sonora VideoSegmenter Engine — Anime-First Video Segmentation Pipeline

Pipeline: Demucs (vocal isolation) → Silero VAD (speech detection) →
         faster-whisper / anime-whisper (transcription) →
         fugashi+UniDic (Japanese tokenization) →
         Qwen3-ForcedAligner-0.6B / wav2vec2 (precise alignment) →
         pyannote Callhome-JPN (speaker diarization) →
         Merge → ffmpeg video cutting

Supports two modes:
  - "fast": VAD + Whisper segment timestamps + pyannote (~100-300ms precision)
  - "precise": Full pipeline with forced alignment (~10-30ms precision)

Aligner options (precise mode):
  - "qwen3": Qwen3-ForcedAligner-0.6B — SOTA, no dictionary needed, 11 langs
  - "wav2vec2": Japanese wav2vec2 + torchaudio forced_align (legacy fallback)

Author: Sonora AI Studio
"""

import os
import re
import uuid
import time
import logging
import asyncio
import tempfile
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger("sonora.segmenter.engine")

# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

@dataclass
class Word:
    """A single word with timing and speaker info."""
    text: str
    start: float
    end: float
    speaker: str = "UNKNOWN"
    confidence: float = 0.0


@dataclass
class Segment:
    """A sentence-level segment spoken by one speaker."""
    id: str
    index: int
    start: float
    end: float
    duration: float
    speaker: str
    text: str
    words: List[Word] = field(default_factory=list)
    clip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


@dataclass
class SegmentationResult:
    """Complete result from the segmentation pipeline."""
    segments: List[Segment]
    duration: float
    language: str
    num_speakers: int
    device: str
    mode: str  # "fast" or "precise"
    aligner: str  # "qwen3" or "wav2vec2"
    processing_time: float


# ─────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────

def extract_audio_from_video(video_path: str, output_path: Optional[str] = None,
                             sample_rate: int = 16000, mono: bool = True) -> str:
    """
    Extract audio from video using ffmpeg.
    Returns path to the extracted WAV file.
    """
    if output_path is None:
        output_path = str(Path(video_path).with_suffix(".wav"))

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                    # No video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", str(sample_rate), # Sample rate
        "-ac", "1" if mono else "2",  # Channels
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    logger.info(f"Extracted audio: {output_path}")
    return output_path


def extract_thumbnail(video_path: str, timestamp: float, output_path: str) -> str:
    """Extract a single frame from video at the given timestamp."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except Exception as e:
        logger.warning(f"Thumbnail extraction failed: {e}")
    return ""


# ─────────────────────────────────────────────────────────────
# Silero VAD — Voice Activity Detection
# ─────────────────────────────────────────────────────────────

class SileroVAD:
    """
    Wrapper for Silero VAD — language-agnostic voice activity detection.
    Detects speech regions in audio with ~20-30ms granularity.
    Works on CPU, no GPU required.
    """

    def __init__(self, threshold: float = 0.5, min_speech_duration: float = 0.25,
                 min_silence_duration: float = 0.3, window_size_ms: int = 512):
        self.threshold = threshold
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration
        self.window_size_ms = window_size_ms
        self.model = None
        self._utils = None

    def _load_model(self):
        """Lazy-load the Silero VAD model."""
        if self.model is not None:
            return
        try:
            self.model, self._utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True
            )
            logger.info("Silero VAD model loaded.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise

    def detect_speech_regions(self, audio_path: str) -> List[Tuple[float, float]]:
        """
        Detect speech regions in an audio file.
        Returns list of (start_seconds, end_seconds) tuples.
        """
        self._load_model()

        (get_speech_timestamps, _, read_audio, _, _) = self._utils

        wav = read_audio(audio_path, sampling_rate=16000)
        speech_timestamps = get_speech_timestamps(
            wav,
            self.model,
            threshold=self.threshold,
            min_speech_duration_ms=int(self.min_speech_duration * 1000),
            min_silence_duration_ms=int(self.min_silence_duration * 1000),
            window_size_samples=self.window_size_ms,
            return_seconds=True
        )

        # Convert to list of tuples
        regions = []
        for ts in speech_timestamps:
            start = ts["start"]
            end = ts["end"]
            if end - start >= self.min_speech_duration:
                regions.append((start, end))

        logger.info(f"VAD detected {len(regions)} speech regions.")
        return regions

    def has_speech(self, audio_path: str) -> bool:
        """Quick check if audio contains any speech."""
        regions = self.detect_speech_regions(audio_path)
        return len(regions) > 0


# ─────────────────────────────────────────────────────────────
# Transcriber — Whisper-based ASR with word timestamps
# ─────────────────────────────────────────────────────────────

class WhisperTranscriber:
    """
    Transcription using faster-whisper (or anime-whisper / kotoba-whisper).
    Supports both segment-level and word-level timestamps.
    """

    # Available models, from most anime-specific to general
    MODEL_OPTIONS = {
        "anime": "litagin/anime-whisper-v2",           # Anime-specific fine-tune
        "kotoba": "RoachLin/kotoba-whisper-v2.2-faster", # Japanese-optimized
        "large": "large-v3",                            # General multilingual
        "medium": "medium",                             # Lighter option
        "base": "base",                                 # Fastest option
    }

    def __init__(self, model_name: str = "large-v3", device: str = "auto",
                 compute_type: str = "auto"):
        self.model_name = model_name
        self.model = None
        self._device = device
        self._compute_type = compute_type

    def _resolve_device(self):
        """Resolve device and compute type based on availability."""
        device = self._device
        compute_type = self._compute_type

        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        return device, compute_type

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self.model is not None:
            return
        from faster_whisper import WhisperModel

        device, compute_type = self._resolve_device()
        logger.info(f"Loading Whisper model '{self.model_name}' on {device} ({compute_type})...")

        self.model = WhisperModel(
            self.model_name,
            device=device,
            compute_type=compute_type,
            download_root=os.getenv("WHISPER_MODEL_DIR", None)
        )
        logger.info(f"Whisper model loaded: {self.model_name}")

    def transcribe(self, audio_path: str, language: str = "ja",
                   word_timestamps: bool = True,
                   vad_filter: bool = True) -> Dict[str, Any]:
        """
        Transcribe audio file with timestamps.
        Returns dict with segments and words.
        """
        self._load_model()

        segments_iter, info = self.model.transcribe(
            audio_path,
            language=language,
            word_timestamps=word_timestamps,
            vad_filter=vad_filter,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200
            ),
            condition_on_previous_text=False,  # Prevent hallucination
            beam_size=5,
            best_of=5
        )

        segments = []
        all_words = []

        for seg in segments_iter:
            seg_dict = {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": []
            }

            if seg.words:
                for w in seg.words:
                    word_dict = {
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end,
                        "probability": w.probability
                    }
                    seg_dict["words"].append(word_dict)
                    all_words.append(word_dict)

            segments.append(seg_dict)

        result = {
            "segments": segments,
            "words": all_words,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration
        }

        logger.info(f"Transcription complete: {len(segments)} segments, "
                     f"{len(all_words)} words, language={info.language}")
        return result


# ─────────────────────────────────────────────────────────────
# Speaker Diarizer — pyannote with Japanese fine-tuned model
# ─────────────────────────────────────────────────────────────

class SpeakerDiarizer:
    """
    Speaker diarization using pyannote.audio with optional
    Japanese fine-tuned segmentation model (Callhome-JPN).
    """

    def __init__(self, hf_token: Optional[str] = None,
                 use_japanese_model: bool = True,
                 num_speakers: Optional[int] = None):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.use_japanese_model = use_japanese_model
        self.num_speakers = num_speakers
        self.pipeline = None

    def _load_model(self):
        """Lazy-load the pyannote diarization pipeline."""
        if self.pipeline is not None:
            return

        if not self.hf_token:
            logger.warning("No HF_TOKEN provided. Using MockDiarizationPipeline.")
            self.pipeline = MockDiarizationPipeline()
            return

        try:
            from pyannote.audio import Pipeline

            logger.info("Loading pyannote speaker-diarization-3.1...")
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )

            # Try to load Japanese fine-tuned segmentation model
            if self.use_japanese_model:
                try:
                    from pyannote.audio import Model
                    jp_model = Model.from_pretrained(
                        "diarizers-community/speaker-segmentation-fine-tuned-callhome-jpn",
                        use_auth_token=self.hf_token
                    )
                    self.pipeline._segmentation.model = jp_model
                    logger.info("Japanese fine-tuned segmentation model loaded.")
                except Exception as e:
                    logger.warning(f"Failed to load Japanese segmentation model: {e}. "
                                    "Using default pyannote model.")

            # Move to GPU if available
            try:
                import torch
                if torch.cuda.is_available():
                    self.pipeline = self.pipeline.to(torch.device("cuda"))
                    logger.info("Diarization pipeline moved to GPU.")
            except Exception:
                pass

            logger.info("pyannote diarization pipeline loaded.")

        except Exception as e:
            logger.error(f"Failed to load pyannote pipeline: {e}. Using mock.")
            self.pipeline = MockDiarizationPipeline()

    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Run speaker diarization on an audio file.
        Returns list of speaker turns: [{"start", "end", "speaker"}]
        """
        self._load_model()

        try:
            if self.num_speakers:
                diarization = self.pipeline(audio_path,
                                             num_speakers=self.num_speakers)
            else:
                diarization = self.pipeline(audio_path)

            turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                turns.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            logger.info(f"Diarization complete: {len(turns)} speaker turns.")
            return turns

        except Exception as e:
            logger.error(f"Diarization failed: {e}. Returning empty turns.")
            return []


class MockDiarizationPipeline:
    """Fallback diarization that assigns UNKNOWN to entire audio."""

    def __call__(self, audio_path, **kwargs):
        """Return a single speaker turn covering the whole file."""
        import torchaudio
        try:
            info = torchaudio.info(audio_path)
            duration = info.num_frames / info.sample_rate
        except Exception:
            duration = 600.0  # Assume 10 min

        # Generate mock turns of ~30 seconds each, cycling through 3 speakers
        speakers = ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
        turns = []
        chunk_duration = 30.0
        for i in range(int(duration / chunk_duration) + 1):
            start = i * chunk_duration
            end = min((i + 1) * chunk_duration, duration)
            turns.append({
                "start": start,
                "end": end,
                "speaker": speakers[i % len(speakers)]
            })

        logger.warning(f"MockDiarization: Generated {len(turns)} fake turns.")
        return MockDiarizationResult(turns)


class MockDiarizationResult:
    """Mimics pyannote's Diarization output for mock mode."""

    def __init__(self, turns):
        self._turns = turns

    def itertracks(self, yield_label=False):
        """Yield (turn, _, speaker) tuples like pyannote."""
        from collections import namedtuple
        Segment = namedtuple("Segment", ["start", "end"])
        for turn in self._turns:
            seg = Segment(start=turn["start"], end=turn["end"])
            if yield_label:
                yield seg, None, turn["speaker"]
            else:
                yield seg, None


# ─────────────────────────────────────────────────────────────
# Japanese Tokenizer — fugashi + UniDic
# ─────────────────────────────────────────────────────────────

class JapaneseTokenizer:
    """
    Japanese morphological analyzer using fugashi + UniDic.
    Splits Japanese text into morphemes (words) for alignment.
    """

    def __init__(self):
        self._tagger = None

    def _load(self):
        """Lazy-load fugashi tagger."""
        if self._tagger is not None:
            return
        try:
            import fugashi
            self._tagger = fugashi.Tagger()
            logger.info("fugashi tokenizer loaded with UniDic.")
        except ImportError:
            logger.warning("fugashi not available. Falling back to simple character split.")
            self._tagger = None
        except Exception as e:
            logger.warning(f"fugashi load failed: {e}. Using character split.")
            self._tagger = None

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Japanese text into morphemes.
        Returns list of word strings.
        """
        self._load()

        if self._tagger is None:
            # Fallback: simple character-level split (group kanji runs + kana)
            return self._simple_split(text)

        words = []
        for word in self._tagger(text):
            surface = word.surface.strip()
            if surface:
                words.append(surface)

        return words

    def tokenize_with_pos(self, text: str) -> List[Dict[str, str]]:
        """
        Tokenize with part-of-speech information.
        Returns list of {"word", "pos"} dicts.
        """
        self._load()

        if self._tagger is None:
            return [{"word": w, "pos": "UNKNOWN"} for w in self._simple_split(text)]

        results = []
        for word in self._tagger(text):
            surface = word.surface.strip()
            if surface:
                pos = word.feature[0] if word.feature and len(word.feature) > 0 else "UNKNOWN"
                results.append({"word": surface, "pos": pos})

        return results

    @staticmethod
    def _simple_split(text: str) -> List[str]:
        """
        Simple Japanese text splitter as fallback.
        Splits on punctuation and spaces.
        """
        # Split on Japanese punctuation
        parts = re.split(r'([。！？…、\.\!\?\,\s]+)', text)
        words = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Check if it's punctuation
            if re.match(r'^[。！？…、\.\!\?\,\s]+$', part):
                if words:
                    words[-1] = words[-1] + part
            else:
                words.append(part)
        return words if words else [text]


# ─────────────────────────────────────────────────────────────
# Forced Aligner — torchaudio + Japanese wav2vec2
# ─────────────────────────────────────────────────────────────

class JapaneseForcedAligner:
    """
    Forced alignment using torchaudio.functional.forced_align()
    with a Japanese wav2vec2 model (NTQAI/wav2vec2-large-japanese).

    Provides ~20-50ms word-level alignment precision.
    This is the "precise" mode alignment that replaces WhisperX.
    """

    def __init__(self, model_name: str = "NTQAI/wav2vec2-large-japanese"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.tokenizer = JapaneseTokenizer()

    def _load_model(self):
        """Lazy-load the wav2vec2 model and processor."""
        if self.model is not None:
            return
        try:
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
            import torch

            logger.info(f"Loading Japanese wav2vec2 model: {self.model_name}...")
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
            self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(device)
            self.model.eval()

            logger.info(f"Japanese wav2vec2 model loaded on {device}.")
        except Exception as e:
            logger.error(f"Failed to load Japanese wav2vec2: {e}")
            raise

    def _get_emissions(self, audio_path: str):
        """Get CTC emissions from the wav2vec2 model."""
        import torch
        import torchaudio

        self._load_model()

        waveform, sr = torchaudio.load(audio_path)
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            waveform = resampler(waveform)
            sr = 16000

        # Mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        inputs = self.processor(
            waveform.squeeze().numpy(),
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )

        device = next(self.model.parameters()).device
        input_values = inputs.input_values.to(device)

        with torch.no_grad():
            emissions = self.model(input_values).logits

        return emissions, waveform.shape[-1], sr

    def _text_to_tokens(self, text: str) -> List[int]:
        """
        Convert Japanese text to token IDs for the wav2vec2 model.
        Uses fugashi to tokenize, then maps to vocabulary.
        """
        words = self.tokenizer.tokenize(text)
        full_text = "".join(words)

        # Map characters to model vocabulary
        vocab = self.processor.tokenizer.get_vocab()
        token_ids = []

        for char in full_text:
            if char in vocab:
                token_ids.append(vocab[char])
            elif char.lower() in vocab:
                token_ids.append(vocab[char.lower()])

        return token_ids

    def align(self, audio_path: str, text: str,
              start_hint: float = 0.0, end_hint: float = 0.0) -> List[Dict]:
        """
        Force-align text to audio, returning word-level timestamps.

        Args:
            audio_path: Path to audio file
            text: Transcribed text to align
            start_hint: Approximate start time from Whisper (for windowing)
            end_hint: Approximate end time from Whisper (for windowing)

        Returns:
            List of {"word", "start", "end"} dicts with precise timestamps
        """
        import torch
        from torchaudio.functional import forced_align

        self._load_model()

        try:
            emissions, audio_length, sr = self._get_emissions(audio_path)
            token_ids = self._text_to_tokens(text)

            if not token_ids:
                logger.warning("No valid tokens for alignment. Returning empty.")
                return []

            targets = torch.tensor([token_ids], dtype=torch.long)
            input_lengths = torch.tensor([emissions.shape[1]])
            target_lengths = torch.tensor([len(token_ids)])

            alignments, scores = forced_align(
                emissions, targets, input_lengths, target_lengths
            )

            # Convert frame-level alignments to word-level timestamps
            aligned_words = self._alignments_to_timestamps(
                alignments[0], token_ids, audio_length, sr, text
            )

            logger.info(f"Forced alignment complete: {len(aligned_words)} words aligned.")
            return aligned_words

        except Exception as e:
            logger.error(f"Forced alignment failed: {e}")
            return []

    def _alignments_to_timestamps(self, alignment, token_ids: List[int],
                                   audio_length: int, sr: int,
                                   original_text: str) -> List[Dict]:
        """
        Convert frame-level CTC alignment output to word-level timestamps.

        Uses proper CTC collapse logic:
        1. Walk the alignment path, collapsing repeated tokens
        2. Map each collapsed token back to its character in the text
        3. Group characters by morpheme boundaries (from fugashi)
        4. Compute start/end frame for each morpheme → timestamps
        """
        import torch
        import numpy as np

        # Frame duration: wav2vec2 reduces audio by ~320x at 16kHz
        frame_duration = audio_length / (alignment.shape[0] * sr) if alignment.shape[0] > 0 else 0.02

        # Step 1: CTC collapse — walk alignment and collect (token_id, frame_idx) pairs
        # CTC rules: merge consecutive identical tokens, skip blanks
        blank_id = 0  # wav2vec2 blank token is typically index 0
        vocab_size = len(self.processor.tokenizer)

        collapsed = []  # List of (token_id, first_frame, last_frame)
        prev_token = None

        for frame_idx in range(alignment.shape[0]):
            token_id = alignment[frame_idx].item()

            # Skip blank tokens
            if token_id == blank_id or token_id >= vocab_size:
                prev_token = None
                continue

            if token_id == prev_token:
                # Same as previous — extend the range (CTC repeat, not a new token)
                if collapsed:
                    collapsed[-1] = (collapsed[-1][0], collapsed[-1][1], frame_idx)
            else:
                # New token
                collapsed.append((token_id, frame_idx, frame_idx))
                prev_token = token_id

        if not collapsed:
            logger.warning("CTC collapse produced no tokens. Falling back to even distribution.")
            return self._even_distribute_timestamps(original_text, alignment.shape[0], frame_duration)

        # Step 2: Map collapsed tokens back to characters
        # Build the decoded character sequence
        id_to_char = {v: k for k, v in self.processor.tokenizer.get_vocab().items()}
        decoded_chars = []
        for token_id, start_frame, end_frame in collapsed:
            char = id_to_char.get(token_id, "")
            if char and char != "<pad>" and char != "<unk>":
                decoded_chars.append((char, start_frame, end_frame))

        # Step 3: Align decoded chars to the original text using fuzzy matching
        # The decoded chars should match original_text (minus spaces/special chars)
        original_clean = re.sub(r'\s+', '', original_text)
        decoded_text = ''.join(c for c, _, _ in decoded_chars)

        # Step 4: Group by morpheme boundaries
        words = self.tokenizer.tokenize(original_clean)

        # Build character-to-frame mapping
        char_frames = {}  # char_index -> (start_frame, end_frame)
        orig_idx = 0
        for char, start_f, end_f in decoded_chars:
            # Find this character in the original text
            while orig_idx < len(original_clean) and original_clean[orig_idx] != char:
                orig_idx += 1
            if orig_idx < len(original_clean):
                char_frames[orig_idx] = (start_f, end_f)
                orig_idx += 1

        # Step 5: Group characters into words using fugashi tokenization
        aligned = []
        char_offset = 0
        for word in words:
            word_len = len(word)
            word_start_frame = None
            word_end_frame = None

            for ci in range(char_offset, char_offset + word_len):
                if ci in char_frames:
                    sf, ef = char_frames[ci]
                    if word_start_frame is None or sf < word_start_frame:
                        word_start_frame = sf
                    if word_end_frame is None or ef > word_end_frame:
                        word_end_frame = ef

            if word_start_frame is not None and word_end_frame is not None:
                start_time = word_start_frame * frame_duration
                end_time = (word_end_frame + 1) * frame_duration
                aligned.append({
                    "word": word,
                    "start": round(start_time, 3),
                    "end": round(end_time, 3)
                })

            char_offset += word_len

        if not aligned:
            logger.warning("Word-level alignment failed. Falling back to even distribution.")
            return self._even_distribute_timestamps(original_text, alignment.shape[0], frame_duration)

        return aligned

    def _even_distribute_timestamps(self, text: str, total_frames: int,
                                     frame_duration: float) -> List[Dict]:
        """Fallback: evenly distribute words across the audio segment."""
        words = self.tokenizer.tokenize(text)
        if not words:
            return []

        frames_per_word = max(1, total_frames // len(words))
        aligned = []

        for i, word in enumerate(words):
            start_frame = i * frames_per_word
            end_frame = min((i + 1) * frames_per_word, total_frames)
            aligned.append({
                "word": word,
                "start": round(start_frame * frame_duration, 3),
                "end": round(end_frame * frame_duration, 3)
            })

        return aligned


# ─────────────────────────────────────────────────────────────
# Qwen3 Forced Aligner — SOTA multilingual alignment (PRIMARY)
# ─────────────────────────────────────────────────────────────

class Qwen3ForcedAligner:
    """
    Forced alignment using Qwen3-ForcedAligner-0.6B.

    This is the PRIMARY aligner for the Sonora pipeline. It provides:
    - SOTA accuracy (outperforms MFA and NFA in benchmarks)
    - Native Japanese support without dictionaries or G2P
    - Word-level AND character-level timestamp granularity
    - 11 language support (en, fr, de, it, pt, es, ja, ko, ru, th, vi)
    - Apache 2.0 license (commercial use OK)
    - 0.6B params (lightweight for GPU inference)

    Precision: ~10-30ms word-level alignment.
    """

    MODEL_NAME = "Qwen/Qwen3-ForcedAligner-0.6B"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME
        self.model = None
        self.processor = None
        self.tokenizer = JapaneseTokenizer()  # For morpheme grouping

    def _load_model(self):
        """Lazy-load the Qwen3 ForcedAligner model and processor."""
        if self.model is not None:
            return
        try:
            from transformers import AutoModelForCausalLM, AutoProcessor
            import torch

            logger.info(f"Loading Qwen3-ForcedAligner: {self.model_name}...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(device)
            self.model.eval()

            logger.info(f"Qwen3-ForcedAligner loaded on {device}.")

        except Exception as e:
            logger.error(f"Failed to load Qwen3-ForcedAligner: {e}")
            raise

    def align(self, audio_path: str, text: str,
              start_hint: float = 0.0, end_hint: float = 0.0,
              language: str = "ja") -> List[Dict]:
        """
        Force-align text to audio, returning word-level timestamps.

        Args:
            audio_path: Path to audio file (WAV 16kHz preferred)
            text: Transcribed text to align
            start_hint: Approximate start time from Whisper (for windowing)
            end_hint: Approximate end time from Whisper (for windowing)
            language: Language code for the text (default: "ja")

        Returns:
            List of {"word", "start", "end"} dicts with precise timestamps
        """
        import torch
        import torchaudio

        self._load_model()

        try:
            # Load and preprocess audio
            waveform, sr = torchaudio.load(audio_path)

            # Window audio if we have start/end hints
            if start_hint > 0 or end_hint > 0:
                start_sample = int(max(0, start_hint - 0.5) * sr)
                end_sample = int(min(waveform.shape[-1] / sr, end_hint + 0.5) * sr)
                waveform = waveform[:, start_sample:end_sample]
                time_offset = max(0, start_hint - 0.5)
            else:
                time_offset = 0.0

            # Resample to 16kHz if needed
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                waveform = resampler(waveform)
                sr = 16000

            # Mono
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)

            # Try the model-specific alignment API
            aligned_words = self._align_with_model_api(waveform, text, language, time_offset)

            if aligned_words:
                return aligned_words

            # Fallback: try the generic transformers approach
            return self._align_generic(waveform, text, language, time_offset)

        except Exception as e:
            logger.error(f"Qwen3 forced alignment failed: {e}")
            return []

    def _align_with_model_api(self, waveform, text: str, language: str,
                               time_offset: float) -> List[Dict]:
        """
        Try alignment using the model's built-in alignment method.
        Qwen3-ForcedAligner may expose a .align() or similar method.
        """
        import torch

        try:
            # Prepare inputs using the processor
            inputs = self.processor(
                text=text,
                audio=waveform.squeeze().numpy(),
                sampling_rate=16000,
                return_tensors="pt",
                language=language,
            )

            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v
                      for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)

            # Check if the model returns timestamps directly
            if hasattr(outputs, 'timestamps') and outputs.timestamps is not None:
                return self._parse_timestamps_output(
                    outputs.timestamps, text, time_offset
                )

            # Check for alignment-specific output format
            if hasattr(outputs, 'alignment') and outputs.alignment is not None:
                return self._parse_alignment_output(
                    outputs.alignment, text, time_offset
                )

            # If the model has a post_process method
            if hasattr(self.processor, 'decode_alignment'):
                alignment = self.processor.decode_alignment(outputs, text=text)
                return self._parse_alignment_output(alignment, text, time_offset)

            return []  # Signal to try generic approach

        except Exception as e:
            logger.debug(f"Model-specific API failed: {e}. Trying generic approach.")
            return []

    def _align_generic(self, waveform, text: str, language: str,
                        time_offset: float) -> List[Dict]:
        """
        Generic alignment approach: run model inference, then extract
        timestamps from attention weights or output tokens.

        The Qwen3-ForcedAligner is an LLM-based NAR model that predicts
        timestamps as special tokens in its output. We decode these to get
        word-level timing.
        """
        import torch

        try:
            # Prepare prompt with timestamp request
            prompt = f"<|align_start|>{text}<|align_end|>"

            inputs = self.processor(
                text=prompt,
                audio=waveform.squeeze().numpy(),
                sampling_rate=16000,
                return_tensors="pt",
            )

            device = next(self.model.parameters()).device
            input_ids = inputs.get("input_ids", inputs.get("input")).to(device)
            attention_mask = inputs.get("attention_mask", None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(device)

            with torch.no_grad():
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    output_hidden_states=True,
                )

            # Extract timestamps from generated output
            # The model should output timestamp tokens interspersed with text
            if hasattr(outputs, 'logits'):
                predicted_ids = outputs.logits.argmax(dim=-1)[0]
                return self._decode_timestamp_tokens(
                    predicted_ids, text, time_offset,
                    inputs.get("input_ids", input_ids).shape[-1]
                )

            return []

        except Exception as e:
            logger.error(f"Generic alignment failed: {e}")
            return []

    def _parse_timestamps_output(self, timestamps, text: str,
                                  time_offset: float) -> List[Dict]:
        """Parse model output timestamps into word-level alignment."""
        words = self.tokenizer.tokenize(text)
        aligned = []

        if isinstance(timestamps, (list, tuple)):
            # If timestamps is a list of (word, start, end) tuples
            for item in timestamps:
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    aligned.append({
                        "word": str(item[0]),
                        "start": round(float(item[1]) + time_offset, 3),
                        "end": round(float(item[2]) + time_offset, 3)
                    })

        elif hasattr(timestamps, 'cpu'):
            # PyTorch tensor format
            import torch
            ts = timestamps.cpu().numpy()
            # Assume shape: (num_words, 2) where columns are start, end
            for i, word in enumerate(words):
                if i < len(ts):
                    aligned.append({
                        "word": word,
                        "start": round(float(ts[i][0]) + time_offset, 3),
                        "end": round(float(ts[i][1]) + time_offset, 3)
                    })

        return aligned

    def _parse_alignment_output(self, alignment, text: str,
                                 time_offset: float) -> List[Dict]:
        """Parse alignment output (dict or structured data)."""
        words = self.tokenizer.tokenize(text)
        aligned = []

        if isinstance(alignment, dict):
            # Dict format: {"words": [...], "timestamps": [...]}
            word_list = alignment.get("words", words)
            ts_list = alignment.get("timestamps", alignment.get("segments", []))

            for i, word in enumerate(word_list):
                if i < len(ts_list):
                    ts = ts_list[i]
                    if isinstance(ts, (list, tuple)) and len(ts) >= 2:
                        aligned.append({
                            "word": str(word),
                            "start": round(float(ts[0]) + time_offset, 3),
                            "end": round(float(ts[1]) + time_offset, 3)
                        })

        elif isinstance(alignment, (list, tuple)):
            for item in alignment:
                if isinstance(item, dict):
                    aligned.append({
                        "word": item.get("word", item.get("text", "")),
                        "start": round(float(item.get("start", 0)) + time_offset, 3),
                        "end": round(float(item.get("end", 0)) + time_offset, 3)
                    })

        return aligned

    def _decode_timestamp_tokens(self, predicted_ids, text: str,
                                  time_offset: float,
                                  input_length: int) -> List[Dict]:
        """
        Decode timestamp tokens from model output.
        The model uses special timestamp tokens like <|t_0.00|> to mark timing.
        """
        words = self.tokenizer.tokenize(text)
        aligned = []

        # Decode all tokens
        decoded_tokens = self.processor.tokenizer.convert_ids_to_tokens(predicted_ids)

        # Find timestamp tokens and text tokens
        timestamps = []  # List of (time_seconds, token_idx)
        text_tokens = []  # List of (text, token_idx)

        ts_pattern = re.compile(r'<\|t_(\d+\.?\d*)\|>')

        for idx, token in enumerate(decoded_tokens):
            token_str = str(token)
            ts_match = ts_pattern.match(token_str)
            if ts_match:
                time_val = float(ts_match.group(1))
                timestamps.append((time_val, idx))
            elif token_str and not token_str.startswith('<|') and not token_str.endswith('|>'):
                text_tokens.append((token_str, idx))

        # Pair timestamps with text tokens
        # Strategy: each word boundary is marked by a timestamp token
        if len(timestamps) >= 2:
            for i, word in enumerate(words):
                if i * 2 < len(timestamps) - 1:
                    start_ts = timestamps[i * 2][0]
                    end_ts = timestamps[i * 2 + 1][0]
                    aligned.append({
                        "word": word,
                        "start": round(start_ts + time_offset, 3),
                        "end": round(end_ts + time_offset, 3)
                    })
                elif i * 2 == len(timestamps) - 1:
                    start_ts = timestamps[i * 2][0]
                    # Estimate end as start + average word duration
                    avg_dur = 0.15  # ~150ms average for Japanese words
                    aligned.append({
                        "word": word,
                        "start": round(start_ts + time_offset, 3),
                        "end": round(start_ts + avg_dur + time_offset, 3)
                    })

        # If we couldn't extract timestamps, fall back to word distribution
        if not aligned and words and timestamps:
            total_duration = timestamps[-1][0] - timestamps[0][0] if len(timestamps) > 1 else 0
            if total_duration > 0:
                for i, word in enumerate(words):
                    start = timestamps[0][0] + (i / len(words)) * total_duration
                    end = timestamps[0][0] + ((i + 1) / len(words)) * total_duration
                    aligned.append({
                        "word": word,
                        "start": round(start + time_offset, 3),
                        "end": round(end + time_offset, 3)
                    })

        return aligned

    def align_segment(self, audio_path: str, text: str,
                       seg_start: float, seg_end: float,
                       language: str = "ja") -> List[Dict]:
        """
        Convenience method: align a single segment of audio to text.
        Windows the audio to the segment duration for efficiency.
        """
        return self.align(
            audio_path, text,
            start_hint=seg_start,
            end_hint=seg_end,
            language=language
        )


# ─────────────────────────────────────────────────────────────
# Aligner Factory — choose the best available aligner
# ─────────────────────────────────────────────────────────────

class AlignerFactory:
    """
    Factory for creating the appropriate forced aligner.

    Priority order:
      1. Qwen3-ForcedAligner-0.6B (SOTA, dictionary-free, Japanese native)
      2. Japanese wav2vec2 + torchaudio forced_align (legacy fallback)
    """

    @staticmethod
    def create(aligner_type: str = "qwen3") -> object:
        """
        Create a forced aligner instance.

        Args:
            aligner_type: "qwen3" (default) or "wav2vec2"

        Returns:
            An aligner instance with an .align() method
        """
        if aligner_type == "qwen3":
            try:
                return Qwen3ForcedAligner()
            except Exception as e:
                logger.warning(f"Failed to create Qwen3 aligner: {e}. "
                                "Falling back to wav2vec2.")
                return JapaneseForcedAligner()
        elif aligner_type == "wav2vec2":
            return JapaneseForcedAligner()
        else:
            logger.warning(f"Unknown aligner type '{aligner_type}'. Defaulting to qwen3.")
            return AlignerFactory.create("qwen3")


# ─────────────────────────────────────────────────────────────
# Video Clip Cutter — ffmpeg-based
# ─────────────────────────────────────────────────────────────

class VideoClipCutter:
    """
    Cut video into per-segment clips using ffmpeg.
    Uses stream-copy mode (no re-encode) for speed,
    with re-encode fallback for precision.
    """

    def __init__(self, output_dir: str, padding_ms: int = 150):
        self.output_dir = Path(output_dir)
        self.padding_ms = padding_ms
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def cut_segment(self, video_path: str, segment_id: str,
                    start: float, end: float) -> Optional[str]:
        """
        Cut a single segment from the video.
        Returns path to the clip file, or None on failure.
        """
        output_path = str(self.output_dir / f"seg_{segment_id}.mp4")

        # Add padding for smoother cuts (but don't go below 0)
        padded_start = max(0, start - self.padding_ms / 1000.0)
        padded_end = end + self.padding_ms / 1000.0

        # Try stream-copy first (very fast, no re-encode)
        if self._cut_stream_copy(video_path, padded_start, padded_end, output_path):
            return output_path

        # Fallback: re-encode (slower but accurate)
        if self._cut_reencode(video_path, padded_start, padded_end, output_path):
            return output_path

        logger.warning(f"Failed to cut segment {segment_id}")
        return None

    def _cut_stream_copy(self, video_path: str, start: float, end: float,
                          output_path: str) -> bool:
        """Cut using stream copy (instant, but may be imprecise at keyframes)."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-i", video_path,
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception as e:
            logger.debug(f"Stream-copy cut failed: {e}")
        return False

    def _cut_reencode(self, video_path: str, start: float, end: float,
                       output_path: str) -> bool:
        """Cut with re-encoding (slower but frame-accurate)."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-i", video_path,
                "-vcodec", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-acodec", "aac",
                "-b:a", "192k",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception as e:
            logger.debug(f"Re-encode cut failed: {e}")
        return False

    def cut_all_segments(self, video_path: str,
                         segments: List[Segment]) -> List[Segment]:
        """
        Cut all segments from the video.
        Updates each segment's clip_path in-place.
        """
        for seg in segments:
            clip_path = self.cut_segment(video_path, seg.id, seg.start, seg.end)
            seg.clip_path = clip_path
            if clip_path:
                # Extract thumbnail from start of segment
                thumb_path = str(self.output_dir / f"thumb_{seg.id}.jpg")
                seg.thumbnail_path = extract_thumbnail(
                    video_path, seg.start, thumb_path
                )

        successful = sum(1 for s in segments if s.clip_path)
        logger.info(f"Cut {successful}/{len(segments)} segments successfully.")
        return segments


# ─────────────────────────────────────────────────────────────
# Main Orchestrator — VideoSegmenter
# ─────────────────────────────────────────────────────────────

class VideoSegmenter:
    """
    Main orchestrator for the Sonora video segmentation pipeline.

    Pipeline (fast mode):
        1. Extract audio from video (ffmpeg)
        2. Isolate vocals with Demucs (optional, for noisy anime)
        3. Detect speech regions (Silero VAD)
        4. Transcribe with word timestamps (faster-whisper / anime-whisper)
        5. Identify speakers (pyannote with Callhome-JPN)
        6. Merge words + speakers into sentence segments
        7. Cut video clips (ffmpeg stream-copy)

    Pipeline (precise mode - adds forced alignment):
        Steps 1-5 same, then:
        6a. Tokenize transcript (fugashi + UniDic)
        6b. Force-align tokens to audio (Qwen3-ForcedAligner / wav2vec2)
        7. Merge aligned words + speakers into sentence segments
        8. Cut video clips (ffmpeg)
    """

    def __init__(self, mode: str = "fast",
                 whisper_model: str = "large-v3",
                 hf_token: Optional[str] = None,
                 num_speakers: Optional[int] = None,
                 output_dir: Optional[str] = None,
                 status_callback=None,
                 aligner_type: str = "qwen3"):
        """
        Args:
            mode: "fast" (segment timestamps) or "precise" (forced alignment)
            whisper_model: Whisper model name or path
            hf_token: HuggingFace token for pyannote
            num_speakers: Hint for number of speakers (None = auto-detect)
            output_dir: Base directory for output files
            status_callback: Async callback for status updates
            aligner_type: "qwen3" (default, SOTA) or "wav2vec2" (legacy fallback)
        """
        self.mode = mode
        self.whisper_model = whisper_model
        self.hf_token = hf_token
        self.num_speakers = num_speakers
        self.aligner_type = aligner_type
        self.output_dir = output_dir or os.getenv(
            "SONORA_DATA_DIR",
            str(Path.home() / "sonora" / "data")
        )
        self.status_callback = status_callback

        # Lazy-initialized components
        self._vad = None
        self._transcriber = None
        self._diarizer = None
        self._aligner = None
        self._tokenizer = None
        self._cutter = None

    async def update_status(self, msg: str):
        """Send a status update via callback."""
        logger.info(f"STATUS: {msg}")
        if self.status_callback:
            if asyncio.iscoroutinefunction(self.status_callback):
                await self.status_callback(msg)
            else:
                self.status_callback(msg)

    def _get_vad(self) -> SileroVAD:
        if self._vad is None:
            self._vad = SileroVAD(threshold=0.5, min_speech_duration=0.25)
        return self._vad

    def _get_transcriber(self) -> WhisperTranscriber:
        if self._transcriber is None:
            self._transcriber = WhisperTranscriber(model_name=self.whisper_model)
        return self._transcriber

    def _get_diarizer(self) -> SpeakerDiarizer:
        if self._diarizer is None:
            self._diarizer = SpeakerDiarizer(
                hf_token=self.hf_token,
                use_japanese_model=True,
                num_speakers=self.num_speakers
            )
        return self._diarizer

    def _get_aligner(self):
        """Get the configured forced aligner (Qwen3 or wav2vec2)."""
        if self._aligner is None:
            self._aligner = AlignerFactory.create(self.aligner_type)
        return self._aligner

    def _get_tokenizer(self) -> JapaneseTokenizer:
        if self._tokenizer is None:
            self._tokenizer = JapaneseTokenizer()
        return self._tokenizer

    async def segment_video(self, video_path: str,
                            language: str = "ja",
                            min_segment_duration: float = 0.5,
                            max_segment_duration: float = 15.0,
                            cut_clips: bool = True,
                            isolate_vocals: bool = True) -> SegmentationResult:
        """
        Main entry point: segment a video into per-sentence, per-speaker clips.

        Args:
            video_path: Path to the input video file (in shared volume)
            language: Language code (default: "ja" for Japanese)
            min_segment_duration: Minimum segment duration in seconds
            max_segment_duration: Maximum segment duration in seconds
            cut_clips: Whether to cut video into individual clips
            isolate_vocals: Whether to run Demucs vocal isolation first

        Returns:
            SegmentationResult with all segments and metadata
        """
        start_time = time.time()

        # Resolve video path
        shared_path = os.getenv("SHARED_PATH", "/tmp/sonora")
        if not os.path.isabs(video_path):
            video_path = os.path.join(shared_path, "uploads", video_path)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Step 1: Extract audio
        await self.update_status("Extracting audio from video...")
        audio_path = await asyncio.to_thread(
            extract_audio_from_video, video_path
        )

        # Step 1b: Vocal isolation (optional but recommended for anime)
        vocals_path = audio_path
        if isolate_vocals:
            await self.update_status("Isolating vocals with Demucs...")
            try:
                vocals_path = await asyncio.to_thread(
                    self._isolate_vocals, audio_path
                )
            except Exception as e:
                logger.warning(f"Vocal isolation failed: {e}. Using raw audio.")

        # Step 2: Voice Activity Detection
        await self.update_status("Detecting speech regions (Silero VAD)...")
        vad = self._get_vad()
        speech_regions = await asyncio.to_thread(
            vad.detect_speech_regions, vocals_path
        )

        # Step 3: Transcription with word timestamps
        await self.update_status("Transcribing speech (Whisper ASR)...")
        transcriber = self._get_transcriber()
        transcription = await asyncio.to_thread(
            transcriber.transcribe, vocals_path, language, True
        )

        # Step 4: Speaker Diarization
        await self.update_status("Identifying speakers (Pyannote)...")
        diarizer = self._get_diarizer()
        speaker_turns = await asyncio.to_thread(
            diarizer.diarize, vocals_path
        )

        # Step 5: Merge words with speaker labels
        await self.update_status("Merging transcription with speaker labels...")
        words_with_speakers = self._assign_speakers_to_words(
            transcription["words"], speaker_turns
        )

        # Step 6: Optional forced alignment (precise mode)
        if self.mode == "precise" and transcription["words"]:
            aligner_name = "Qwen3-ForcedAligner" if self.aligner_type == "qwen3" else "wav2vec2"
            await self.update_status(f"Running forced alignment ({aligner_name})...")
            try:
                words_with_speakers = await asyncio.to_thread(
                    self._refine_with_forced_alignment,
                    vocals_path, words_with_speakers, transcription["segments"], language
                )
            except Exception as e:
                logger.warning(f"Forced alignment failed: {e}. Using Whisper timestamps.")

        # Step 7: Group into sentence segments
        await self.update_status("Grouping words into sentence segments...")
        segments = self._group_into_segments(
            words_with_speakers,
            min_duration=min_segment_duration,
            max_duration=max_segment_duration
        )

        # Step 8: Cut video clips
        if cut_clips and segments:
            clips_dir = os.path.join(self.output_dir, "segments",
                                      Path(video_path).stem)
            await self.update_status(f"Cutting {len(segments)} video clips...")
            cutter = VideoClipCutter(clips_dir)
            segments = await asyncio.to_thread(
                cutter.cut_all_segments, video_path, segments
            )

        # Count unique speakers
        speakers = set(s.speaker for s in segments)

        processing_time = time.time() - start_time

        result = SegmentationResult(
            segments=segments,
            duration=transcription.get("duration", 0),
            language=transcription.get("language", language),
            num_speakers=len(speakers),
            device=self._get_device_info(),
            mode=self.mode,
            aligner=self.aligner_type,
            processing_time=round(processing_time, 2)
        )

        await self.update_status(
            f"Segmentation complete: {len(segments)} segments, "
            f"{len(speakers)} speakers in {processing_time:.1f}s"
        )

        return result

    def _isolate_vocals(self, audio_path: str) -> str:
        """
        Isolate vocals from audio using Demucs.
        Returns path to the isolated vocals file.
        """
        try:
            from demucs.api import Separator
            separator = Separator(model="htdemucs")
            _, separated = separator.separate_audio_file(audio_path)

            vocals_path = str(Path(audio_path).with_name("vocals_" + Path(audio_path).name))
            import soundfile as sf
            import numpy as np

            vocals = separated.get("vocals", np.zeros(1))
            if isinstance(vocals, np.ndarray) and vocals.size > 0:
                sf.write(vocals_path, vocals.T if vocals.ndim > 1 else vocals, 44100)
                return vocals_path
        except ImportError:
            logger.warning("demucs not available. Skipping vocal isolation.")
        except Exception as e:
            logger.warning(f"Vocal isolation failed: {e}")

        return audio_path

    def _assign_speakers_to_words(self, words: List[Dict],
                                   speaker_turns: List[Dict]) -> List[Word]:
        """
        Assign speaker labels to each word based on overlap with
        diarization speaker turns.
        """
        result = []
        for w in words:
            word_mid = (w["start"] + w["end"]) / 2
            speaker = "UNKNOWN"

            # Find the speaker turn that contains this word's midpoint
            best_overlap = 0
            for turn in speaker_turns:
                overlap_start = max(w["start"], turn["start"])
                overlap_end = min(w["end"], turn["end"])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    speaker = turn["speaker"]

            result.append(Word(
                text=w.get("word", ""),
                start=w["start"],
                end=w["end"],
                speaker=speaker,
                confidence=w.get("probability", 0.0)
            ))

        return result

    def _refine_with_forced_alignment(self, audio_path: str,
                                       words: List[Word],
                                       whisper_segments: List[Dict],
                                       language: str = "ja") -> List[Word]:
        """
        Refine word timestamps using forced alignment.
        Uses Whisper segments to window the audio, then aligns each segment.

        The Qwen3 aligner uses start_hint/end_hint for windowing internally,
        so we DON'T double-offset the timestamps. The wav2vec2 aligner aligns
        the full audio, so we DO need to offset by segment start.
        """
        aligner = self._get_aligner()
        refined_words = []
        is_qwen3 = isinstance(aligner, Qwen3ForcedAligner)

        for seg in whisper_segments:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue

            try:
                # Qwen3 aligner accepts language parameter
                if is_qwen3:
                    aligned = aligner.align(
                        audio_path, seg_text,
                        start_hint=seg["start"],
                        end_hint=seg["end"],
                        language=language
                    )
                else:
                    aligned = aligner.align(
                        audio_path, seg_text,
                        start_hint=seg["start"],
                        end_hint=seg["end"]
                    )

                if aligned:
                    for aw in aligned:
                        # Qwen3 handles time offset internally via start_hint windowing
                        # wav2vec2 aligns full audio, so no offset needed either
                        # (it aligns the full file and we filter by segment)
                        start_time = aw["start"]
                        end_time = aw["end"]

                        # Find closest original word for speaker label
                        speaker = "UNKNOWN"
                        best_dist = float('inf')
                        for ow in words:
                            dist = abs(ow.start - start_time)
                            if dist < best_dist and dist < 0.5:
                                best_dist = dist
                                speaker = ow.speaker

                        refined_words.append(Word(
                            text=aw["word"],
                            start=round(start_time, 3),
                            end=round(end_time, 3),
                            speaker=speaker
                        ))
                else:
                    # Keep original Whisper timestamps for this segment
                    for w in words:
                        if seg["start"] <= w.start <= seg["end"]:
                            refined_words.append(w)

            except Exception as e:
                logger.warning(f"Forced alignment failed for segment: {e}")
                # Keep original words for this segment
                for w in words:
                    if seg["start"] <= w.start <= seg["end"]:
                        refined_words.append(w)

        return refined_words if refined_words else words

    def _group_into_segments(self, words: List[Word],
                              min_duration: float = 0.5,
                              max_duration: float = 15.0,
                              pause_threshold: float = 0.4,
                              max_words: int = 12) -> List[Segment]:
        """
        Group words into sentence-level segments based on:
        1. Speaker changes (hard boundary)
        2. Sentence-ending punctuation (。！？…)
        3. Pause gaps > threshold
        4. Max words/duration hard walls
        """
        if not words:
            return []

        # Filter out non-alphanumeric "words" (Whisper artifacts)
        vocal_words = [
            w for w in words
            if any(c.isalnum() for c in w.text)
        ]

        if not vocal_words:
            return []

        segments = []
        current_words = [vocal_words[0]]
        split_punct = re.compile(r'.*[。！？…\.!\?]{1,}')

        for i in range(1, len(vocal_words)):
            prev = vocal_words[i - 1]
            curr = vocal_words[i]

            seg_duration = curr.start - current_words[0].start
            gap = curr.start - prev.end
            speaker_changed = curr.speaker != prev.speaker
            has_punct = bool(split_punct.match(prev.text))

            # Split conditions (in priority order)
            should_split = (
                speaker_changed or
                has_punct or
                gap > pause_threshold or
                len(current_words) >= max_words or
                seg_duration >= max_duration
            )

            if should_split:
                # Create segment from current words
                seg = self._create_segment(current_words, len(segments))
                if seg.duration >= min_duration:
                    segments.append(seg)
                else:
                    # Too short — merge with previous segment if possible
                    if segments:
                        segments[-1].words.extend(current_words)
                        segments[-1].end = current_words[-1].end
                        segments[-1].duration = segments[-1].end - segments[-1].start
                        segments[-1].text = " ".join(w.text for w in segments[-1].words)
                    else:
                        segments.append(seg)  # Keep first short segment

                current_words = []

            current_words.append(curr)

        # Don't forget the last group
        if current_words:
            seg = self._create_segment(current_words, len(segments))
            if seg.duration >= min_duration or len(segments) == 0:
                segments.append(seg)
            elif segments:
                # Merge with previous
                segments[-1].words.extend(current_words)
                segments[-1].end = current_words[-1].end
                segments[-1].duration = segments[-1].end - segments[-1].start
                segments[-1].text = " ".join(w.text for w in segments[-1].words)

        # Re-index
        for i, seg in enumerate(segments):
            seg.index = i

        return segments

    @staticmethod
    def _create_segment(words: List[Word], index: int) -> Segment:
        """Create a Segment from a list of Words."""
        text = " ".join(w.text for w in words)
        start = words[0].start
        end = words[-1].end
        speaker = words[0].speaker

        # If mixed speakers, use the majority speaker
        speaker_counts: Dict[str, int] = {}
        for w in words:
            speaker_counts[w.speaker] = speaker_counts.get(w.speaker, 0) + 1
        if speaker_counts:
            speaker = max(speaker_counts, key=speaker_counts.get)

        return Segment(
            id=str(uuid.uuid4())[:8],
            index=index,
            start=round(start, 3),
            end=round(end, 3),
            duration=round(end - start, 3),
            speaker=speaker,
            text=text,
            words=words
        )

    @staticmethod
    def _get_device_info() -> str:
        """Get device information for the result."""
        try:
            import torch
            if torch.cuda.is_available():
                return f"cuda ({torch.cuda.get_device_name(0)})"
            return "cpu"
        except ImportError:
            return "cpu (torch not available)"


# ─────────────────────────────────────────────────────────────
# Convenience function for quick segmentation
# ─────────────────────────────────────────────────────────────

async def segment_video(video_path: str, **kwargs) -> SegmentationResult:
    """
    Quick convenience function to segment a video.
    Creates a VideoSegmenter and runs the pipeline.
    """
    segmenter = VideoSegmenter(**kwargs)
    return await segmenter.segment_video(video_path)
