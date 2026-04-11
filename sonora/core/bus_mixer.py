import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("sonora.bus_mixer")

class BusMixer:
    """
    The 'Master Surgeon' of the Sonora pipeline.
    Uses FFmpeg Complex Filtergraphs to surgically replace dialogue
    while preserving environmental audio tracks.
    """
    def __init__(self, video_path: str, output_path: str):
        self.video = video_path
        self.output = output_path
        self.clips = []  # List of dicts: {'path': str, 'start': float}

    def add_clip(self, clip_path: str, start_time: float):
        """Registers a dubbed clip for mixing."""
        self.clips.append({'path': clip_path, 'start': start_time})

    def perform_surgery(
        self, 
        ducking: bool = True, 
        vocal_chat_path: Optional[str] = None,
        emotional_cues_path: Optional[str] = None,
        background_songs_path: Optional[str] = None,
        background_music_path: Optional[str] = None
    ) -> str:
        """
        Executes the 'Four-Stem Surgery' mix:
        1. Layers Background Music & Songs (Opera).
        2. Layers original Emotional Cues (Laughs/Gasps).
        3. Layers new AI Dubbing clips.
        4. Applies sidechain ducking only where necessary.
        """
        if not self.clips:
            logger.warning("No clips to mix. Returning original video.")
            return self.video

        # Prepare inputs for FFmpeg
        # [0:v] is video, [0:a] is original audio (not used in surgery)
        # We add the 4 stem inputs explicitly if provided
        inputs = ['-i', self.video]
        stem_indices = {}
        curr_idx = 1
        
        for name, path in [
            ("chat", vocal_chat_path), 
            ("cues", emotional_cues_path), 
            ("songs", background_songs_path), 
            ("music", background_music_path)
        ]:
            if path and os.path.exists(path):
                inputs.extend(['-i', path])
                stem_indices[name] = curr_idx
                curr_idx += 1
            else:
                logger.info(f"Stem '{name}' not found at {path}, skipping.")
        
        # Add the dubbing clips
        dub_start_idx = curr_idx
        for clip in self.clips:
            inputs.extend(['-i', clip['path']])
            curr_idx += 1

        # --- Filter Setup ---
        filter_parts = []
        
        # 1. Background Stems (Music & Songs)
        # Apply ducking to music and songs if needed
        bg_labels = []
        if "music" in stem_indices:
            bg_labels.append(f"[{stem_indices['music']}:a]")
        if "songs" in stem_indices:
            bg_labels.append(f"[{stem_indices['songs']}:a]")
        
        if bg_labels:
            # Sidechain Ducking Filter
            duck_parts = []
            for c in self.clips:
                d = self._get_duration(c['path'])
                if d > 0:
                    duck_parts.append(f"between(t,{c['start']:.3f},{c['start']+d:.3f})")
            
            duck_conditions = " + ".join(duck_parts)
            bg_mix = "".join(bg_labels) + f"amix=inputs={len(bg_labels)}:duration=first[raw_bg]"
            filter_parts.append(bg_mix)
            
            if ducking and duck_parts:
                filter_parts.append(f"[raw_bg]volume=enable='{duck_conditions}':volume=0.25[ducked_bg]")
                bg_final = "[ducked_bg]"
            else:
                bg_final = "[raw_bg]"
        else:
            # Fallback if no bg stems: Mute original dialogue from video track
            mute_filter = "[0:a]"
            for i, clip in enumerate(self.clips):
                duration = self._get_duration(clip['path'])
                mute_filter += f"volume=enable='between(t,{clip['start']:.3f},{clip['start']+duration:.3f})':volume=0"
                if i < len(self.clips) - 1: mute_filter += ","
            filter_parts.append(mute_filter + "[bg_fallback]")
            bg_final = "[bg_fallback]"

        # 2. Cues & Dubs (The Spoken Layer)
        layer_labels = [bg_final]
        
        # Add original emotional cues (untouched by volume ducking)
        if "cues" in stem_indices:
            layer_labels.append(f"[{stem_indices['cues']}:a]")
            
        # Add new AI dubs with precision delays
        for i, clip in enumerate(self.clips):
            delay_ms = int(clip['start'] * 1000)
            label = f"d{i}"
            filter_parts.append(f"[{dub_start_idx + i}:a]adelay={delay_ms}|{delay_ms}[{label}]")
            layer_labels.append(f"[{label}]")

        # 3. Final Master Mix
        amix_filter = f"{''.join(layer_labels)}amix=inputs={len(layer_labels)}:duration=first:dropout_transition=0[out_a]"
        filter_parts.append(amix_filter)

        filter_complex = "; ".join(filter_parts)

        # Final Assembly CMD
        cmd = [
            'ffmpeg', '-y', *inputs,
            '-filter_complex', filter_complex,
            '-map', '0:v', 
            '-map', '[out_a]',
            '-c:v', 'copy', 
            '-c:a', 'aac', '-b:a', '192k',
            self.output
        ]
        
        logger.info(f"Executing FFmpeg surgery for {len(self.clips)} segments...")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return self.output
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Surgery Failed: {e.stderr.decode()}")
            raise

    def _get_duration(self, path: str) -> float:
        """Utility to get duration via ffprobe."""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', path
            ], capture_output=True, text=True, check=True)
            return float(result.stdout)
        except Exception:
            return 0.0