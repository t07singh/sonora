
import streamlit as st
import os
import sys
from pathlib import Path

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from sonora.core.orchestrator import SonoraOrchestrator, group_words_by_pause, count_syllables, estimate_japanese_morae
    from sonora.editor_ui import AudioEditorUI
except ImportError as e:
    st.error(f"Failed to import Sonora core components: {e}")
    st.stop()

st.set_page_config(page_title="Sonora AI Studio", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
    .sync-ok { color: #10b981; font-weight: 800; font-size: 0.8rem; }
    .sync-drift { color: #f59e0b; font-weight: 800; font-size: 0.8rem; }
    .stCodeBlock { background-color: #0f172a !important; }
    .render-area { border-top: 2px solid #eee; padding-top: 2rem; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)


def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dubbing Studio", "Audio Editor"])

    if page == "Dubbing Studio":
        render_studio_page()
    elif page == "Audio Editor":
        render_editor_page()

def render_editor_page():
    # Attempt to retrieve the path from the session state (from Studio Ingestion)
    audio_path = st.session_state.get('secure_path', None)
    
    # Initialize and render the editor
    editor = AudioEditorUI(audio_path)
    editor.render()

def render_studio_page():
    st.title("🎙️ Sonora AI: Surgical Dubbing Suite")
    st.caption("v5.2 Production Release | Precision Script Adaptation")

    if 'segments' not in st.session_state: st.session_state.segments = None
    if 'translations' not in st.session_state: st.session_state.translations = []
    if 'voice_id' not in st.session_state: st.session_state.voice_id = "21m00Tcm4TlvDq8ikWAM"

    with st.sidebar:
        st.header("🎞️ Studio Ingestion")
        video_file = st.file_uploader("Upload Anime Source (MP4)", type=["mp4", "mov"])
        st.session_state.voice_id = st.text_input("ElevenLabs Voice ID", value=st.session_state.voice_id)
        char_tone = st.selectbox("Persona Style", ["Dramatic Shonen", "Casual Slice of Life", "Villainous Deep"])
        
        st.divider()
        if st.button("🧹 Reset Project"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    if not video_file:
        st.info("👋 Welcome. Please upload a video clip to begin.")
        return

    # Ingestion & Initial Analysis
    if st.session_state.segments is None:
        if st.button("🔍 Run Isometric Analysis", type="primary"):
            with st.spinner("🕵️ Analyzing dialogue flaps..."):
                orchestrator = SonoraOrchestrator(video_file)
                raw_data = orchestrator.run_transcription()
                st.session_state.segments = group_words_by_pause(raw_data)
                st.session_state.secure_path = orchestrator.audio_path
                
                translations = []
                for seg in st.session_state.segments:
                    translations.append(orchestrator.translate_segment(seg, char_tone))
                st.session_state.translations = translations
                st.rerun()

    # The Script Cockpit
    if st.session_state.segments:
        st.header("🎬 Surgical Script Editor")
        
        for idx, seg in enumerate(st.session_state.segments):
            col_time, col_edit, col_sync = st.columns([1, 4, 1])
            
            start_t = seg[0]['start']
            end_t = seg[-1]['end']
            japanese_text = " ".join([w['word'] for w in seg])
            target_flaps = estimate_japanese_morae(japanese_text)
            
            with col_time:
                st.code(f"{start_t:.2f}s → {end_t:.2f}s")
                st.caption(f"Target: {target_flaps} flaps")

            with col_edit:
                st.session_state.translations[idx] = st.text_input(
                    f"Line {idx+1}", 
                    value=st.session_state.translations[idx], 
                    key=f"input_{idx}"
                )
            
            with col_sync:
                current_flaps = count_syllables(st.session_state.translations[idx])
                diff = abs(current_flaps - target_flaps)
                if diff <= 1:
                    st.markdown("<p class='sync-ok'>✅ SYNC OK</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p class='sync-drift'>⚠️ DRIFT ({current_flaps})</p>", unsafe_allow_html=True)
                    if st.button("🪄 Refactor", key=f"fix_{idx}"):
                        orch = SonoraOrchestrator(st.session_state.secure_path)
                        st.session_state.translations[idx] = orch.refactor_line(st.session_state.translations[idx], target_flaps, char_tone)
                        st.rerun()

        # Final Render Section
        st.markdown('<div class="render-area">', unsafe_allow_html=True)
        if st.button("🎬 RENDER FINAL STUDIO MASTER", type="primary", use_container_width=True):
            with st.spinner("Executing Final Assembly Pipeline..."):
                try:
                    orch = SonoraOrchestrator(st.session_state.secure_path)
                    final_path = orch.assemble_final_dub(
                        st.session_state.segments, 
                        st.session_state.translations,
                        voice_id=st.session_state.voice_id
                    )
                    st.session_state.last_master = final_path
                    st.success("🎉 Rendering Complete!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Render Failure: {e}")
        
        if 'last_master' in st.session_state:
            st.video(st.session_state.last_master)
            with open(st.session_state.last_master, "rb") as f:
                st.download_button("📥 Download Dubbed Master", f, file_name=f"sonora_dub_{video_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

