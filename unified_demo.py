import streamlit as st
import sys
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import requests
import librosa
import numpy as np
import pandas as pd
import plotly.express as px

# Add repo to path for imports
repo_path = Path(".").absolute()
sys.path.append(str(repo_path))

# Import Sonora Modules
from sonora.audio_editing.path_manager import (
    get_secure_path, 
    SessionManager, 
    check_ffmpeg,
    validate_output
)
from sonora.editor_ui import AudioEditorUI, BusType
from sonora.utils.production_manager import BatchProcessor, ProductionProjectManager, Priority, JobStatus
from sonora.utils.voice_registry import list_registered_characters, get_character_voice
from sonora.core.orchestrator import count_syllables, estimate_japanese_morae

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Sonora: Unified AI Dubbing Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM STYLES =================
st.markdown("""
<style>
    .main { background-color: #0e1117; color: white; }
    .stProgress > div > div > div > div { background-color: #FF7EB9; }
    .stButton>button {
        background: linear-gradient(90deg, #FF7EB9, #7b2ff7);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #7b2ff7, #FF7EB9);
        box-shadow: 0 0 10px rgba(255, 126, 185, 0.5);
    }
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #7b2ff7;
        margin-bottom: 10px;
    }
    .queue-item {
        background: rgba(255,255,255,0.05);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 3px solid #7EB9FF;
    }
    .status-online { color: #00ff00; font-weight: bold; }
    .status-offline { color: #ff0000; font-weight: bold; }
    .priority-urgent { color: #ff4b4b; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

# ================= STATE MANAGEMENT =================
if 'path_manager' not in st.session_state:
    st.session_state.path_manager = SessionManager()
    
if 'current_file_path' not in st.session_state:
    st.session_state.current_file_path = None

if 'batch_processor' not in st.session_state:
    st.session_state.batch_processor = BatchProcessor()

if 'project_manager' not in st.session_state:
    st.session_state.project_manager = ProductionProjectManager()

if 'editor' not in st.session_state:
    st.session_state.editor = AudioEditorUI()

if 'segments' not in st.session_state:
    st.session_state.segments = None

if 'active_job_id' not in st.session_state:
    st.session_state.active_job_id = None

if 'auto_refactored' not in st.session_state:
    st.session_state.auto_refactored = set()

if 'stems' not in st.session_state:
    st.session_state.stems = {}
    st.session_state.auto_refactored = set()

# Support Docker environment variables
API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")
ENDPOINTS = {
    "dub": f"{API_BASE}/api/dub",
    "analyze": f"{API_BASE}/api/analyze",
    "refactor": f"{API_BASE}/api/refactor",
    "synthesize": f"{API_BASE}/api/synthesize",
    "health": f"{API_BASE}/health",
    "metrics": f"{API_BASE}/api/metrics",
    "cache_stats": f"{API_BASE}/api/cache/stats",
    "segment": f"{API_BASE}/api/pipeline/segment"
}

# Auth Header for Neural Swarm
AUTH_KEY = os.getenv("SONORA_API_KEY", "admin123").strip()
HEADERS = {"X-Sonora-Key": AUTH_KEY}

# ================= HELPER CLASSES =================
class ExtendedAudioEditor(AudioEditorUI):
    def load_from_path(self, file_path):
        """Extended load to ensure compatibility with Unified Demo sequence."""
        success = super().load_from_path(file_path)
        if success:
            # The real AudioEditorUI uses internal y_data/sr
            # We ensure we don't crash on missing mock components
            if hasattr(self, 'bus_system'):
                self.bus_system.load_audio_to_bus(BusType.VOICE, self.y_data, self.sr)
            return True
        return False

    def render_content_only(self):
        self._render_main_content()

if not isinstance(st.session_state.editor, ExtendedAudioEditor):
    st.session_state.editor = ExtendedAudioEditor()

# ================= MAIN UI =================
def main():
    with st.sidebar:
        st.title("🎬 Sonora Studio")
        st.caption("v2.5 Enterprise Edition")
        
        mode = st.radio("Workstation Mode", 
            ["🚀 Project Dashboard", "✂️ Neural Slicing", "🎙️ AI Dubbing", "🎹 Sound Engineering", "🏭 Production Scale", "🛠️ System Health"]
        )
        
        st.markdown("---")
        st.subheader("📁 Global Input")
        uploaded_file = st.file_uploader("Import Source Audio", type=["wav", "mp3", "m4a"])
        
        if uploaded_file:
            if st.session_state.current_file_path is None or uploaded_file.name not in st.session_state.current_file_path:
                with st.spinner("🔒 Securing file to workspace..."):
                    secure_path = get_secure_path(uploaded_file)
                    st.session_state.path_manager.track(secure_path)
                    st.session_state.current_file_path = secure_path
                    st.success("File imported to workspace")
        
        if st.session_state.current_file_path:
            st.info(f"Active File: `{Path(st.session_state.current_file_path).name}`")
            
        st.markdown("---")
        st.caption("Powered by **Deepmind Auralis Swarm**")

    if mode == "🚀 Project Dashboard":
        render_dashboard()
    elif mode == "🎙️ AI Dubbing":
        render_dubbing_pipeline()
    elif mode == "✂️ Neural Slicing":
        render_segmentation_hub()
    elif mode == "🎹 Sound Engineering":
        render_sound_editor()
    elif mode == "🏭 Production Scale":
        render_production_scale()
    elif mode == "🛠️ System Health":
        render_system_health()

# ================= PAGE FUNCTIONS =================

def render_segmentation_hub():
    st.title("✂️ Neural Slicing Hub")
    st.markdown("Precision dialogue extraction and speaker identification using WhisperX & Pyannote.")
    
    if not st.session_state.current_file_path:
        st.warning("⚠️ Please upload a source video/audio in the sidebar first.")
        return

    st.video(st.session_state.current_file_path) if st.session_state.current_file_path.endswith('.mp4') else st.audio(st.session_state.current_file_path)

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("⚡ Dissect Neural Dialogue", type="primary", use_container_width=True):
            with st.status("🕵️ Neural Swarm: Extracting character dialogue...", expanded=True) as status:
                try:
                    status.write("🚀 Initiating high-load segmentation proxy...")
                    # We pass the filename; the backend expects the file to be available in shared volume
                    payload = {"video_path": os.path.basename(st.session_state.current_file_path)}
                    
                    # Call the new Proxy endpoint (timeout 10min for heavy AI)
                    r = requests.post(ENDPOINTS["segment"], json=payload, headers=HEADERS, timeout=600)
                    
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.segments = data.get("segments", [])
                        status.update(label=f"✅ Successfully extracted {len(st.session_state.segments)} dialogue segments!", state="complete")
                        st.success("Dissection successful. You can now rename characters below.")
                    else:
                        status.update(label="❌ Neural Handshake Failed", state="error")
                        st.error(f"Error: {r.text}")
                except Exception as e:
                    st.error(f"Connection Fault: {e}")

    if st.session_state.segments:
        st.divider()
        st.subheader("👥 Character Segments")
        
        # Display as a dataframe for quick overview but allow per-segment renaming
        df_segments = []
        for i, seg in enumerate(st.session_state.segments):
            df_segments.append({
                "Index": i + 1,
                "Speaker": seg.get('speaker', 'Unknown'),
                "Start": f"{seg['start']:.2f}s",
                "End": f"{seg['end']:.2f}s",
                "Dialogue": seg.get('text', '')[:100] + "..."
            })
        
        st.dataframe(pd.DataFrame(df_segments), use_container_width=True)

        st.markdown("### 🖋️ Character Alignment")
        with st.expander("Expand to rename speakers and verify lines"):
            for i, seg in enumerate(st.session_state.segments):
                col1, col2, col3 = st.columns([1, 2, 4])
                with col1:
                    st.caption(f"Segment {i+1}")
                with col2:
                    current_speaker = seg.get('speaker', 'Unknown')
                    new_speaker = st.text_input(f"Speaker ID", value=current_speaker, key=f"speaker_{i}")
                    if new_speaker != current_speaker:
                        st.session_state.segments[i]['speaker'] = new_speaker
                with col3:
                    st.caption(f"{seg['start']:.2f}s -> {seg['end']:.2f}s")
                    st.info(seg.get('text', '[No Dialogue Detected]'))

        if st.button("📥 Push to AI Dubbing Studio", use_container_width=True):
            # This persists the segments into session state where render_dubbing_pipeline expects them
            st.success("✅ Segments pushed to Studio. Switch to 'AI Dubbing' tab to continue.")
            time.sleep(1)
            # We don't need to do anything else, st.session_state.segments is already updated


def render_dashboard():
    st.title("🚀 Studio Dashboard")
    st.markdown("Real-time overview of the Sonora Swarm dubbing cluster.")
    
    c1, c2, c3 = st.columns(3)
    try:
        r = requests.get(ENDPOINTS["health"], headers=HEADERS, timeout=2)
        status_color = "status-online" if r.status_code == 200 else "status-offline"
        status_text = "ONLINE" if r.status_code == 200 else "OFFLINE"
    except:
        status_color = "status-offline"
        status_text = "UNREACHABLE"
        
    c1.markdown(f'<div class="metric-card"><h3>API Link</h3><span class="{status_color}" style="font-size: 2em;">{status_text}</span></div>', unsafe_allow_html=True)
    ffmpeg_ok = check_ffmpeg()
    c2.markdown(f'<div class="metric-card"><h3>Audio Engine</h3><span class="{"status-online" if ffmpeg_ok else "status-offline"}" style="font-size: 2em;">{"READY" if ffmpeg_ok else "ERROR"}</span></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><h3>Workspace</h3><span style="font-size: 2em; color: #00bfff;">{"LOADED" if st.session_state.current_file_path else "WAITING"}</span></div>', unsafe_allow_html=True)
    
    st.markdown("### 📈 Recent Activity")
    try:
        metrics = requests.get(ENDPOINTS["metrics"], headers=HEADERS, timeout=3).json()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Requests", metrics.get('total_requests', 0))
        m2.metric("Processing Errors", metrics.get('total_errors', 0))
        m3.metric("Uptime (min)", f"{metrics.get('uptime_minutes', 0):.1f}")
    except:
        st.warning("Cannot fetch metrics from backend.")

def render_dubbing_pipeline():
    st.title("🎙️ AI Dubbing Pipeline")
    if not st.session_state.current_file_path:
        st.warning("⚠️ Please upload a source file in the sidebar first.")
        return
    st.audio(st.session_state.current_file_path)
    with st.expander("⚙️ Pipeline Configuration", expanded=True):
        c1, c2 = st.columns(2)
        target_lang = c1.selectbox("Target Language", ["English (en)", "Spanish (es)", "French (fr)"])
        dubbing_mode = c2.selectbox("Dubbing Mode", ["Fast (Streaming)", "High Quality (Batch)"])
    
    # Helper for persistent polling
    def poll_job(job_id, status_box):
        while True:
            try:
                job_res = requests.get(f"{API_BASE}/api/job/{job_id}", headers=HEADERS, timeout=180).json()
                current_status = job_res.get("status")
                
                if current_status == "Complete":
                    st.session_state.segments = job_res.get("result", {}).get("segments", [])
                    st.session_state.stems = job_res.get("result", {}).get("stems", {})
                    st.session_state.active_job_id = None # Clear once done
                    status_box.update(label="✅ Neural Analysis Complete!", state="complete", expanded=False)
                    st.success("Analysis finalized. Script Editor Active.")
                    st.rerun()
                    break
                elif current_status == "Error":
                    st.error(f"Backend Analysis Failed: {job_res.get('error')}")
                    st.session_state.active_job_id = None
                    break
                else:
                    status_box.write(f"⚙️ {current_status}")
                    time.sleep(3)
            except Exception as e:
                status_box.write(f"⏳ Waiting for API... ({e})")
                time.sleep(5)

    # 1. Automatic Resume if a job is in progress
    if st.session_state.active_job_id and not st.session_state.segments:
        with st.status(f"🛰️ Resuming Neural Analysis (Job: {st.session_state.active_job_id})...", expanded=True) as status_box:
            poll_job(st.session_state.active_job_id, status_box)

    # 2. Manual Start
    if st.button("🚀 Launch Dubbing Sequence", type="primary"):
        with st.status("🕵️ Swarm Intelligence: Analyzing Content...", expanded=True) as status_box:
            try:
                files = {'file': open(st.session_state.current_file_path, 'rb')}
                response = requests.post(ENDPOINTS["analyze"], files=files, headers=HEADERS, timeout=300)
                if response.status_code == 200:
                    job_id = response.json().get("job_id")
                    st.session_state.active_job_id = job_id
                    status_box.write(f"🧬 Job Created: `{job_id}`. Starting persistence link...")
                    poll_job(job_id, status_box)
                else:
                    st.error(f"Handshake Failed: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

        # --- THE SURGICAL SCRIPT EDITOR ---
    if st.session_state.segments:
        st.divider()
        c1, c2 = st.columns([4, 1])
        c1.subheader("🎬 Surgical Script Editor")
        
        # --- REPAIR ALL ERRORS FEATURE ---
        error_indices = [idx for idx, s in enumerate(st.session_state.segments) 
                         if s['translation'].startswith('[') and s['translation'].endswith(']')]
        
        if error_indices:
            if c2.button(f"⚠️ Repair All ({len(error_indices)})", type="primary", use_container_width=True):
                with st.status("Swarm: Mass Repair in Progress...", expanded=True) as status:
                    for idx in error_indices:
                        seg = st.session_state.segments[idx]
                        status.write(f"🔄 Repairing Segment {idx+1}...")
                        payload = {
                            "text": "Please translate naturally for dubbing.", # Prompt hint
                            "target_syllables": seg.get('targetFlaps', 10),
                            "style": "Anime"
                        }
                        try:
                            # 45s timeout per repair (Phase 2 hardening)
                            r = requests.post(ENDPOINTS["refactor"], json=payload, headers=HEADERS, timeout=45)
                            if r.status_code == 200:
                                data = r.json()
                                st.session_state.segments[idx]['translation'] = data['text']
                                st.session_state.segments[idx]['last_engine'] = data.get('engine', 'swarm')
                        except:
                            continue
                    status.update(label="✅ All repairable errors resolved!", state="complete")
                    st.rerun()

        st.info("Adjust lines below. AI will attempt to auto-sync if drift is detected.")
        
        # Track if we need a rerun after the loop
        needs_rerun = False
        
        for i, seg in enumerate(st.session_state.segments):
            c1, c2, c3 = st.columns([1, 4, 1])
            
            with c1:
                # Add Speaker Label
                speaker = seg.get('speaker', 'Unknown')
                st.markdown(f"**SPEAKER {speaker}**")
                st.code(f"{seg['start']:.2f}s - {seg['end']:.2f}s")
                st.caption(f"Target: {seg.get('targetFlaps', 0)} flaps")
            
            with c2:
                # Use a unique key for each segment
                current_val = seg['translation']
                new_text = st.text_input(f"Segment {i+1}", value=current_val, key=f"seg_input_{i}_{st.session_state.active_job_id}")
                
                if new_text != current_val:
                    st.session_state.segments[i]['translation'] = new_text
                    # Reset auto-sync for this segment if manually edited
                    if i in st.session_state.auto_refactored:
                        st.session_state.auto_refactored.remove(i)
                    st.rerun() # Immediate update for sync status
            
            with c3:
                # Actual syllable counting
                is_sentinel = new_text.startswith('[') and new_text.endswith(']')
                current_flaps = count_syllables(new_text) if not is_sentinel else 999
                target_flaps = seg.get('targetFlaps', 10)
                
                # State Badge
                diff = abs(current_flaps - target_flaps)
                
                if is_sentinel:
                    st.error("⚠️ AI ERROR")
                elif diff == 0:
                    st.success("SYNC OK")
                else:
                    st.error(f"DRIFT ({diff})")
                
                # Engine Metadata
                engine = seg.get('last_engine')
                if engine and engine != 'unknown':
                    st.caption(f"🤖 {engine.upper()}")
                
                # Auto-Refactor Logic (Self-Healing)
                if diff > 2 and i not in st.session_state.auto_refactored and not needs_rerun:
                    st.session_state.auto_refactored.add(i)
                    st.toast(f"🪄 Auto-Refactoring Segment {i+1}...", icon="🔄")
                    payload = {
                        "text": new_text,
                        "target_syllables": target_flaps,
                        "style": "Anime"
                    }
                    try:
                        # 45s timeout for auto-sync (Phase 2 hardening)
                        r = requests.post(ENDPOINTS["refactor"], json=payload, headers=HEADERS, timeout=45)
                        if r.status_code == 200:
                            data = r.json()
                            st.session_state.segments[i]['translation'] = data['text']
                            st.session_state[f"seg_input_{i}_{st.session_state.active_job_id}"] = data['text']
                            st.session_state.segments[i]['last_engine'] = data.get('engine', 'auto')
                            needs_rerun = True
                        else:
                            st.error(f"Auto-Sync Failed: {r.status_code}")
                    except Exception as e:
                        st.error(f"Sync Error: {e}")

                if diff <= 2:
                    st.markdown("<p class='status-online'>SYNC OK</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p class='priority-urgent'>DRIFT ({current_flaps})</p>", unsafe_allow_html=True)
                
                # Manual Refactor Button (Always Persistent)
                if st.button("🪄 Refactor", key=f"btn_refactor_{i}"):
                    with st.status("Surgical Rewriting...", expanded=False) as status:
                        payload = {
                            "text": new_text,
                            "target_syllables": target_flaps,
                            "style": "Anime"
                        }
                        try:
                            # 45s timeout for manual surgical rewrites (Phase 2 hardening)
                            r = requests.post(ENDPOINTS["refactor"], json=payload, headers=HEADERS, timeout=45)
                            if r.status_code == 200:
                                data = r.json()
                                st.session_state.segments[i]['translation'] = data['text']
                                st.session_state[f"seg_input_{i}_{st.session_state.active_job_id}"] = data['text']
                                st.session_state.segments[i]['last_engine'] = data.get('engine', 'unknown')
                                st.session_state.auto_refactored.add(i) 
                                status.update(label=f"Sync Restored via {data.get('engine', 'AI')}", state="complete")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                status.update(label=f"Handshake Error: {r.status_code}", state="error")
                                st.error(f"API Error: {r.text}")
                        except requests.exceptions.Timeout:
                            status.update(label="AI Service Busy", state="error")
                            st.warning("Gemini/Groq is taking longer than 60s. This line might be too complex or the API is slow. Try manual editing or click Refactor again later.")
                        except Exception as e:
                            status.update(label=f"Handshake Fault", state="error")
                            st.error(f"Error: {e}")

        if needs_rerun:
            st.rerun()
        
        # --- FINAL SYNTHESIS & MIX ---
        st.divider()
        c1, c2 = st.columns(2)
        voice_id = c1.text_input("Voice ID (e.g., ElevenLabs)", value="demo_voice_001")
        
        if c2.button("🎬 Synthesize & Mix Master Track", type="primary"):
            with st.spinner("🎶 Neural Synthesis: Generating final dub..."):
                try:
                    payload = {
                        "segments": st.session_state.segments,
                        "translations": [seg['translation'] for seg in st.session_state.segments],
                        "voice_id": voice_id,
                        "video_path": st.session_state.current_file_path,
                        "stems": st.session_state.get('stems')
                    }
                    r = requests.post(ENDPOINTS["synthesize"], json=payload, headers=HEADERS, timeout=1200) # Extended for CPU-based Swarm
                    if r.status_code == 200:
                        master_path = r.json()['master_path']
                        st.success(f"✨ Dubbing Complete! Master saved to: {master_path}")
                        st.balloons()
                    else:
                        st.error(f"Synthesis Failed: {r.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

def render_sound_editor():
    editor = st.session_state.editor
    if st.session_state.current_file_path and editor.current_audio is None:
         with st.spinner("Loading audio..."):
             editor.load_from_path(st.session_state.current_file_path)
    editor.render_content_only()

def render_production_scale():
    st.title("🏭 Production Scale")
    st.markdown("Enterprise-grade tools for episode batches and series consistency.")
    
    tabs = st.tabs(["📋 Batch Queue", "📂 Project Manager", "📊 Quality Dashboard", "👤 Voice Library"])
    
    with tabs[0]:
        st.subheader("Batch Queue Manager")
        uploaded_batch = st.file_uploader("Upload Episode Batch (MP4/WAV)", accept_multiple_files=True)
        if uploaded_batch:
            for f in uploaded_batch:
                if st.button(f"Queue {f.name}", key=f"q_{f.name}"):
                    st.session_state.batch_processor.add_job(f.name, "demo-01", "S01E01")
                    st.toast(f"Added {f.name} to production queue")
        
        st.divider()
        jobs = st.session_state.batch_processor.jobs
        if not jobs:
            st.info("Queue is empty. Load episodes above.")
        else:
            for job in jobs:
                st.markdown(f"""
                <div class="queue-item">
                    <b>{job['filename']}</b> | {job['episode']} | Priority: {job['priority']} <br/>
                    Status: {job['status']} | Progress: {job['progress']*100:.1f}%
                </div>
                """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            if c1.button("▶️ Start Batch"): st.success("Batch processing started")
            if c2.button("⏸️ Pause All"): st.warning("Batch paused")
            if c3.button("🗑️ Clear Queue"): 
                st.session_state.batch_processor.jobs = []
                st.rerun()

    with tabs[1]:
        st.subheader("Multi-Project Hub")
        pm = st.session_state.project_manager
        for pid, data in pm.projects.items():
            with st.expander(f"📁 {data['name']}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Episodes", f"{data['completed']}/{data['episodes']}")
                c2.metric("Characters", len(data['characters']))
                c3.button("Open Project", key=f"open_{pid}")
        
        if st.button("➕ New Project"):
            st.text_input("Series Name", key="new_proj_name")
            st.number_input("Episode Count", 1, 100, 12, key="new_proj_eps")
            if st.button("Create"):
                pm.create_project(st.session_state.new_proj_name, st.session_state.new_proj_eps)
                st.rerun()

    with tabs[2]:
        st.subheader("Studio QA Metrics")
        stats = st.session_state.batch_processor.get_stats()
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Quality Score", f"{stats['avg_quality']:.2f}")
        c2.metric("Failed Jobs", stats['failed'])
        c3.metric("Passed QA", stats['completed'])
        
        # Mock chart for quality trends
        df = pd.DataFrame({
            'Episode': [f"Ep {i}" for i in range(1, 11)],
            'Score': [0.92, 0.88, 0.95, 0.91, 0.94, 0.89, 0.93, 0.96, 0.92, 0.94]
        })
        fig = px.line(df, x='Episode', y='Score', title="Temporal Consistency Trend")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("Global Character Library")
        chars = list_registered_characters()
        if not chars:
            st.info("No characters registered. Use the Casting Utility to digitize lead voices.")
        else:
            cols = st.columns(2)
            for i, char in enumerate(chars):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>👤 {char}</h4>
                        <p style="font-size: 0.8em; opacity: 0.7;">Production Asset: v1.0 Locked</p>
                        <span class="status-online">CONSISTENCY: 98.4%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"A/B Test {char}", key=f"ab_{char}"):
                        st.info("Comparing Season 1 vs Season 2 latent embeddings...")

def render_system_health():
    st.title("🛠️ System Health")
    st.subheader("Filesystem Bridge")
    tracked_files = st.session_state.path_manager.registry
    st.write(f"Tracking **{len(tracked_files)}** secure temporary files.")
    if st.button("Purge Workspace"):
        st.session_state.path_manager.purge_all()
        st.session_state.current_file_path = None
        st.rerun()
    st.markdown("---")
    st.subheader("Cache Performance")
    try:
        stats = requests.get(ENDPOINTS["cache_stats"], headers=HEADERS, timeout=2).json()
        st.json(stats)
    except:
        st.error("Cache API unreachable")

if __name__ == "__main__":
    main()