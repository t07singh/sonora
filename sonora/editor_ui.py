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
        
        # UI State - PERSISTENT across reruns
        if 'separation_results' not in st.session_state:
            st.session_state.separation_results = {}
        
        self.y_data = None
        self.sr = 44100
        
        # Load audio if provided
        if self.audio_path and os.path.exists(self.audio_path):
            self.load_from_path(self.audio_path)

    @property
    def separation_result(self):
        if not self.audio_path: return False
        return st.session_state.separation_results.get(self.audio_path, False)
    
    @separation_result.setter
    def separation_result(self, value):
        if self.audio_path:
            st.session_state.separation_results[self.audio_path] = value

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
            # Reset state for new load
            self.y_data = None
            
            logger.info(f"Attempting to load audio from {audio_path}")
            if not os.path.exists(audio_path):
                logger.error(f"Audio file does not exist: {audio_path}")
                return False
                
            # Use soundfile directly if it's a WAV, as it's faster and more reliable on Windows
            if audio_path.lower().endswith('.wav'):
                self.y_data, self.sr = sf.read(audio_path, always_2d=False)
                # Convert to mono if needed for the editor
                if self.y_data.ndim == 2:
                    self.y_data = (self.y_data[:, 0] + self.y_data[:, 1]) / 2
                logger.info("Loaded WAV via soundfile.")
            else:
                # Fallback to librosa for other formats
                self.y_data, self.sr = librosa.load(self.audio_path, sr=None)
                logger.info("Loaded via librosa.")
                
            return True
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            self.y_data = None # Ensure it doesn't get stuck in a "None" state that triggers reload
            return False

    def render_content_only(self):
        """Compatibility method for unified_demo.py"""
        self._render_main_content()

    def _render_main_content(self):
        """Internal rendering logic for tabs"""
        # Debug Expander (Internal Use)
        with st.expander("🛠️ Internal Debug Diagnostics", expanded=False):
            st.write(f"**Data Dir:** `{get_data_dir()}`")
            st.write(f"**Audio Path:** `{self.audio_path}`")
            st.write(f"**Audio Loaded:** `{self.current_audio is not None}`")
            if self.audio_path:
                st.write(f"**File Exists:** `{os.path.exists(self.audio_path)}`")
                if os.path.exists(self.audio_path):
                    st.write(f"**File Size:** `{os.path.getsize(self.audio_path) / 1024:.1f} KB`")
            
            st.write("**Stem Directory Status:**")
            if self.audio_path:
                stems_dir = get_data_dir() / "stems" / os.path.basename(self.audio_path).replace(".", "_")
                st.code(str(stems_dir))
                if stems_dir.exists():
                    st.write(f"Files: `{os.listdir(stems_dir)}`")
                else:
                    st.write("Directory does not exist yet.")

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
        if not self.audio_path:
            st.info("Please upload an audio file to begin surgical separation.")
            return

        stems_dir = get_data_dir() / "stems" / os.path.basename(self.audio_path).replace(".", "_")
        
        st.subheader("AI Stem Separation (Sound Engineering 2.0)")
        st.markdown("Isolate surgical layers: Spoken Chat, Emotional Cues, Background Songs, and Instrumental Music.")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            model_name = st.selectbox("Separation Model", ["Sound Engineering 2.0 (htdemucs + Isolation)", "Spleeter (Fast)"])
            if st.button("🚀 Separate Stems", type="primary"):
                self._perform_separation(model_name)
                
        with col2:
            if self.separation_result:
                st.success("Surgical Stems Isolated!")
                
                s1, s2 = st.tabs(["🗣️ Vocals / Dialogue", "🎵 Music / Ambient"])
                
                with s1:
                    st.text("Pure Spoken Chat")
                    if os.path.exists(st_chat := str(stems_dir / "vocal_chat.wav")):
                        st.audio(st_chat)
                    
                    st.text("Emotional Cues (Laughs/Cries)")
                    if os.path.exists(st_cues := str(stems_dir / "emotional_cues.wav")):
                        st.audio(st_cues)
                
                with s2:
                    st.text("Background Songs (Opera/Singing)")
                    if os.path.exists(st_songs := str(stems_dir / "background_songs.wav")):
                        st.audio(st_songs)
                        
                    st.text("Instrumental Music")
                    if os.path.exists(st_music := str(stems_dir / "music.wav")):
                        st.audio(st_music)

    def _perform_separation(self, model_name):
        with st.spinner(f"Performing 4-Stem Surgery using {model_name}..."):
            try:
                import asyncio
                from sonora.core.orchestrator import SonoraOrchestrator

                orch = SonoraOrchestrator(self.audio_path)

                # Safe asyncio execution in Streamlit context
                # (avoids conflicts with any existing event loop)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = pool.submit(asyncio.run, orch.run_separation())
                            stems = future.result(timeout=600)
                    else:
                        stems = loop.run_until_complete(orch.run_separation())
                except RuntimeError:
                    stems = asyncio.run(orch.run_separation())

                if not stems or not any(stems.values()):
                    raise RuntimeError(
                        "All cloud separation attempts failed. "
                        "Check your HF_TOKEN and network connection."
                    )

                self.separation_result = True
                st.success("✅ 4-Stem Surgery complete! Stems are ready below.")
                # Minor delay so the success message is visible before rerun
                import time; time.sleep(0.5)
                st.rerun()
            except Exception as e:
                logger.error(f"Separation failed: {e}", exc_info=True)
                st.error(f"❌ Separation failed: {e}")

    def _render_mixing_console(self):
        st.subheader("Professional 4-Track Mixer")
        st.info("Surgically adjust levels for final Master Export.")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.slider("🗣️ Spoken Chat", -60, 10, 0, format="%d dB")
        with c2:
            st.slider("🎭 Emotional Cues", -60, 10, 0, format="%d dB")
        with c3:
            st.slider("🎤 Background Songs", -60, 10, -5, format="%d dB")
        with c4:
            st.slider("🎵 Instr. Music", -60, 10, -3, format="%d dB")
            
        st.markdown("---")
        st.caption("Sidechain ducking is automatically applied to Background Songs & Music where dialogue exists.")

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

