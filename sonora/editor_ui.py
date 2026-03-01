import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import os
import logging
from pathlib import Path
from typing import Optional, Dict

# Import Real Backend Services
try:
    from src.services.separator.audio_separator import AudioSeparator, SeparationModel
    from sonora.core.bus_mixer import BusMixer
    from sonora.audio_editing.path_manager import get_data_dir
except ImportError as e:
    st.error(f"Failed to import Sonora backend services: {e}")
    # Basic mocks to prevent immediate crash if imports fail during dev
    class SeparationModel:
        DEMUCS = "demucs"
        DEMUCS_V4 = "htdemucs"
        SPLEETER = "spleeter"
        CLOUD_DEMUCS = "cloud_demucs"
        SWARM_DEMUCS = "swarm_demucs"
    class AudioSeparator: 
        def __init__(self, **kwargs):
            self.model = "mock"
            logger.warning("⚠️ AudioSeparator running in MOCK mode due to import failure.")
        
        def separate_audio(self, audio_path, **kwargs):
            logger.info(f"🧪 Mock separation triggered for {audio_path}")
            # Return a mock result to match SeparationResult structure
            from dataclasses import dataclass
            @dataclass
            class MockResult:
                voice: np.ndarray
                music: np.ndarray
                sample_rate: int = 44100
            
            # Create small mock audio arrays
            return MockResult(voice=np.zeros(100), music=np.zeros(100))

    class BusMixer: 
        def __init__(self, *args, **kwargs): pass
        def perform_surgery(self, **kwargs): return "mock_fixed.wav"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora.editor_ui")

from enum import Enum
class BusType(Enum):
    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"
    ENVIRONMENT = "environment"
    MASTER = "master"

class AudioEditorUI:
    """
    Standalone Audio Editor Interface for Sonora.
    Connects to:
    - AudioSeparator (Stem Isolation)
    - BusMixer (FFmpeg-based Composing)
    """
    def __init__(self, audio_path: Optional[str] = None):
        self.audio_path = audio_path
        self.audio_separator = AudioSeparator(model=SeparationModel.SWARM_DEMUCS) # Offload to GPU Swarm
        
        # UI State
        self.separation_result = None
        self.y_data = None
        self.sr = 44100
        
        # Load audio if provided
        if self.audio_path and os.path.exists(self.audio_path):
            self.load_from_path(self.audio_path)

    @property
    def current_audio(self):
        return self.y_data
    
    @current_audio.setter
    def current_audio(self, value):
        self.y_data = value

    @property
    def current_sample_rate(self):
        return self.sr
    
    @current_sample_rate.setter
    def current_sample_rate(self, value):
        self.sr = value

    def load_from_path(self, audio_path: str):
        """Loads audio from a file path into the editor state."""
        try:
            self.audio_path = audio_path
            self.y_data, self.sr = librosa.load(self.audio_path, sr=None)
            logger.info(f"Loaded audio from {audio_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return False

    def render_content_only(self):
        """Compatibility method for unified_demo.py"""
        self._render_main_content()

    def _render_main_content(self):
        """Internal rendering logic for tabs"""
        tabs = st.tabs([
            "🌊 Stem Separation", 
            "🎚️ Mixing Console", 
            "✨ Restoration",
            "⚙️ Export"
        ])
        
        with tabs[0]:
            self._render_stem_separation()
        with tabs[1]:
            self._render_mixing_console()
        with tabs[2]:
            self._render_restoration()
        with tabs[3]:
            self._render_export()

    def render(self):
        """Main render method called by app.py"""
        st.header("🎛️ Sonora Audio Editor")
        
        if not self.audio_path:
            st.info("Please upload a video/audio file in the Ingestion sidebar to begin editing.")
            return

        self._render_main_content()

    def _render_stem_separation(self):
        st.subheader("AI Stem Separation")
        st.markdown("Isolate Voice, Music, and SFX using Demucs/Spleeter architectures.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            model_name = st.selectbox("Separation Model", ["Demucs v4 (High Quality)", "Spleeter (Fast)"])
            if st.button("🚀 Separate Stems", type="primary"):
                self._perform_separation(model_name)
                
        with col2:
            if self.separation_result:
                st.success("Stems Separated Successfully!")
                # Display stems
                st.text("Vocals")
                st.audio(self.separation_result.voice, sample_rate=self.separation_result.sample_rate)
                st.text("Background / Music")
                st.audio(self.separation_result.music, sample_rate=self.separation_result.sample_rate)

    def _perform_separation(self, model_name):
        with st.spinner(f"Separating audio using {model_name}..."):
            try:
                # Update model based on selection
                if "Spleeter" in model_name:
                    self.audio_separator.model = SeparationModel.SPLEETER
                else: 
                    self.audio_separator.model = SeparationModel.SWARM_DEMUCS
                
                # Perform separation on the file path
                self.separation_result = self.audio_separator.separate_audio(self.audio_path)
                
            except Exception as e:
                st.error(f"Separation failed: {e}")

    def _render_mixing_console(self):
        st.subheader("Production Mixer")
        st.info("Adjust levels for final Master Export.")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.slider("🗣️ Dialogue Level", -60, 10, 0, format="%d dB")
        with c2:
            st.slider("🎵 Music Level", -60, 10, -3, format="%d dB")
        with c3:
            st.slider("🔊 SFX Level", -60, 10, -5, format="%d dB")
            
        st.markdown("---")
        st.caption("Real-time preview is currently limited to Master Export due to Streamlit constraints.")

    def _render_restoration(self):
        st.subheader("Audio Restoration")
        st.write("Repair clipping, remove noise, and enhance clarity.")
        st.warning("Repair modules are currently in beta.")

    def _render_export(self):
        st.subheader("Master Export")
        if st.button("💾 Render Final Mix"):
            with st.spinner("Rendering with BusMixer..."):
                try:
                    # In a real scenario, we would take the sliders values and separation results
                    # allow BusMixer to combine them.
                    # For now, we perform a simple pass-through mix to demonstrate integration.
                    
                    output_path = str(get_data_dir() / "exports" / f"editor_export_{os.path.basename(self.audio_path)}")
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    mixer = BusMixer(self.audio_path, output_path)
                    # We could add clips here if we had an editing timeline
                    # mixer.add_clip(...) 
                    
                    final_path = mixer.perform_surgery(ducking=True)
                    st.success(f"Export Complete: {final_path}")
                    st.audio(final_path)
                except Exception as e:
                    st.error(f"Export failed: {e}")

