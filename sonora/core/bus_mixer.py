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

    def perform_surgery(self, ducking: bool = True) -> str:
        """
        Executes the surgical mix:
        1. [0:a] Punctures silence in original audio at clip intervals.
        2. [1:a][2:a]... Delays new clips to exact timestamps.
        3. [mix] Sidechain compression (ducking) and final amix.
        """
        if not self.clips:
            logger.warning("No clips to mix. Returning original video.")
            return self.video

        inputs = ['-i', self.video]
        for clip in self.clips:
            inputs.extend(['-i', clip['path']])

        # 1. Background Lane: Mute original dialogue segments
        # Chaining volume filters for precision
        mute_filter = "[0:a]"
        for i, clip in enumerate(self.clips):
            duration = self._get_duration(clip['path'])
            end_time = clip['start'] + duration
            mute_filter += f"volume=enable='between(t,{clip['start']:.3f},{end_time:.3f})':volume=0"
            if i < len(self.clips) - 1:
                mute_filter += ","
        mute_filter += "[bg]"

        # 2. Dub Lanes: Apply adelay to each input clip
        delay_filters = []
        dub_labels = []
        for i, clip in enumerate(self.clips):
            # i+1 because index 0 is the video
            delay_ms = int(clip['start'] * 1000)
            delay_filters.append(f"[{i+1}:a]adelay={delay_ms}|{delay_ms}[d{i}]")
            dub_labels.append(f"[d{i}]")

        # 3. Master Lane: Sidechain Ducking and Final Mix
        # Duck the background by 20% whenever a dub is active (simulated sidechain)
        duck_filter = ""
        if ducking:
            duck_conditions = " + ".join([f"between(t,{c['start']:.3f},{c['start']+self._get_duration(c['path']):.3f})" for c in self.clips])
            duck_filter = f"[bg]volume=enable='{duck_conditions}':volume=0.8[ducked_bg];"
            mix_input_labels = "[ducked_bg]"
        else:
            mix_input_labels = "[bg]"

        amix_filter = f"{''.join(dub_labels)}{mix_input_labels}amix=inputs={len(self.clips)+1}:duration=first:dropout_transition=0[out_a]"

        filter_complex = f"{mute_filter}; {'; '.join(delay_filters)}; {duck_filter} {amix_filter}"

        # Final Assembly
        cmd = [
            'ffmpeg', '-y', *inputs,
            '-filter_complex', filter_complex,
            '-map', '0:v',      # Direct copy of video stream
            '-map', '[out_a]',   # Mapped mixed audio
            '-c:v', 'copy',     # Zero-loss video speed
            '-c:a', 'aac',      # Standard AAC audio
            '-b:a', '192k',     # High fidelity bitrate
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