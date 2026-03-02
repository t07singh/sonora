import streamlit as st
import requests, os, time, json
from streamlit.components.v1 import html
from pathlib import Path
import pandas as pd

# Try to import visualization libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
WS_BASE = os.getenv("WS_BASE", "ws://localhost:8000")

st.set_page_config(page_title="Sonora Dashboard", layout="wide")

# Add health check and auto-reconnect JS
st.markdown("""
<script>
function checkHealth(){
  fetch('/api/health').then(r => {
    if (!r.ok) {
      console.warn("Backend not healthy, reloading in 1s.");
      setTimeout(()=>location.reload(), 1000);
    }
  }).catch(e => {
    console.warn("Health check failed, reload schedule");
    setTimeout(()=>location.reload(), 1500);
  });
}
setInterval(checkHealth, 3000);
</script>
""", unsafe_allow_html=True)

st.title("🎬 Sonora — Advanced AI Dubbing Dashboard (Phase 5-C)")
st.markdown("**Transform Japanese anime videos into emotionally accurate English dubs using cutting-edge AI** 🎌✨")

# Multi-character mode toggle
st.markdown("---")
st.header("🎭 Multi-Character Dubbing")
multichar_mode = st.checkbox("Enable Multi-Character Mode", value=True, help="Automatically detect speakers and assign unique voices")

# Live status box
status_col, actions_col = st.columns([2,1])
with status_col:
    st.header("System Status")

    st.markdown("**Uptime**:")
    uptime_placeholder = st.empty()

    st.markdown("**Pipeline status**")
    pipeline_placeholder = st.empty()

# Try WebSocket via a small JS snippet which forwards to streamlit
ws_js = f"""
<script>
const ws = new WebSocket("{WS_BASE}/ws/status");
ws.onmessage = (evt) => {{
  const data = JSON.parse(evt.data);
  // Post to the streamlit app via window.postMessage
  window.parent.postMessage({{ type: 'SONORA_WS', data }}, "*");
}};
</script>
"""

# This HTML will open a WS. Using Streamlit's html + window.postMessage we can read via st_js_events or other component.
html(ws_js, height=1)

# Simple polling fallback
def poll_status():
    try:
        r = requests.get(API_BASE + "/health", timeout=2)
        return r.json()
    except Exception:
        return {"status": "down", "uptime": 0}

# Poll and update UI
for i in range(3):
    s = poll_status()
    uptime_placeholder.metric("Uptime (s)", int(s.get("uptime",0)))
    pipeline_placeholder.text(json.dumps(s, indent=2))
    time.sleep(0.5)

st.markdown("---")
st.header("🎤 Text-to-Speech (TTS) Generation")

# TTS Provider Selection
tts_provider = st.selectbox(
    "Select TTS Provider",
    ["VibeVoice", "ElevenLabs"],
    index=0,
    help="Choose between Microsoft VibeVoice (local model) or ElevenLabs (cloud API)"
)

# TTS Test Section
st.subheader("Test TTS Generation")
tts_text = st.text_area(
    "Enter text to synthesize:",
    value="Hello! This is a test of the VibeVoice text-to-speech system.",
    height=100
)

col1, col2 = st.columns(2)
with col1:
    tts_emotion = st.selectbox(
        "Emotion",
        ["neutral", "happy", "sad", "angry", "excited", "calm"],
        index=0,
        key="tts_emotion"
    )
    
    tts_tone = st.selectbox(
        "Tone",
        ["normal", "high", "low", "whisper", "shout"],
        index=0,
        key="tts_tone"
    )

with col2:
    tts_speed = st.slider(
        "Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        key="tts_speed"
    )
    
    tts_pitch = st.slider(
        "Pitch",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        key="tts_pitch"
    )

if st.button("🎵 Generate Speech", type="primary"):
    if tts_text.strip():
        with st.spinner(f"Generating speech with {tts_provider}..."):
            try:
                # Prepare request
                request_data = {
                    "text": tts_text,
                    "provider": tts_provider.lower(),
                    "emotion": tts_emotion,
                    "tone": tts_tone,
                    "speed": tts_speed,
                    "pitch": tts_pitch
                }
                
                # Make API call
                response = requests.post(
                    API_BASE + "/api/tts/generate",
                    json=request_data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success("✅ Speech generated successfully!")
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Duration", f"{result.get('duration', 0):.2f}s")
                        with col2:
                            st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                        with col3:
                            rtf = result.get('duration', 0) / result.get('processing_time', 1) if result.get('processing_time', 0) > 0 else 0
                            st.metric("Real-Time Factor", f"{rtf:.2f}x")
                        
                        # Play audio
                        audio_path = result.get("audio_path")
                        if audio_path:
                            # Construct full URL for audio file
                            audio_url = f"{API_BASE}/api/tts/audio/{audio_path}"
                            st.audio(audio_url, format="audio/wav")
                            
                            # Download button
                            audio_response = requests.get(audio_url)
                            if audio_response.status_code == 200:
                                st.download_button(
                                    label="📥 Download Audio",
                                    data=audio_response.content,
                                    file_name=f"tts_{tts_provider.lower()}_{int(time.time())}.wav",
                                    mime="audio/wav"
                                )
                    else:
                        st.error(f"❌ TTS generation failed: {result.get('error', 'Unknown error')}")
                else:
                    st.error(f"❌ API request failed: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("Please enter some text to synthesize.")

st.markdown("---")
st.header("Advanced AI Dubbing")

# Advanced settings
with st.expander("🎛️ Advanced Settings"):
    col1, col2 = st.columns(2)
    
    with col1:
        target_language = st.selectbox(
            "Target Language", 
            ["en", "ja", "ko", "zh", "es", "fr", "de"],
            index=0
        )
        
        voice_id = st.selectbox(
            "Voice Character",
            ["anime_female_01", "anime_male_01", "anime_female_mature"],
            index=0
        )
        
        emotion = st.selectbox(
            "Emotion",
            ["neutral", "happy", "sad", "angry", "excited", "calm"],
            index=0
        )
    
    with col2:
        tone = st.selectbox(
            "Tone",
            ["normal", "high", "low", "whisper", "shout"],
            index=0
        )
        
        lip_sync_model = st.selectbox(
            "Lip-Sync Model",
            ["auto", "wav2lip", "sadtalker", "real_esrgan"],
            index=0
        )
        
        quality_mode = st.selectbox(
            "Quality Mode",
            ["fast", "balanced", "high_quality"],
            index=1
        )

# Real-time processing toggle
enable_realtime = st.checkbox("🚀 Enable Real-time Processing", value=False)

if enable_realtime:
    st.info("Real-time mode will provide live updates via WebSocket during processing")

# File upload
uploaded = st.file_uploader(
    "Upload a video clip for AI dubbing", 
    type=["mp4", "mov", "avi", "mkv"],
    help="Supported formats: MP4, MOV, AVI, MKV"
)

# Multi-character preview
if uploaded and multichar_mode:
    st.subheader("🎭 Multi-Character Preview")
    if st.button("Preview Speaker Detection"):
        with st.spinner("Analyzing speakers..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                r = requests.post(API_BASE + "/api/multichar/preview/diarization", files=files, timeout=60)
                
                if r.status_code == 200:
                    data = r.json()
                    segments = data.get("segments", [])
                    stats = data.get("statistics", {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Speakers Detected", stats.get("total_speakers", 0))
                        st.metric("Total Segments", len(segments))
                    
                    with col2:
                        st.metric("Total Duration", f"{stats.get('total_duration', 0):.1f}s")
                    
                    # Show speaker timeline
                    if segments:
                        st.subheader("Speaker Timeline")
                        timeline_data = []
                        for seg in segments[:10]:  # Show first 10 segments
                            timeline_data.append({
                                "Speaker": seg["speaker"],
                                "Start": f"{seg['start']:.1f}s",
                                "End": f"{seg['end']:.1f}s",
                                "Duration": f"{seg['end'] - seg['start']:.1f}s"
                            })
                        st.dataframe(timeline_data)
                else:
                    st.error(f"Preview failed: {r.text}")
            except Exception as e:
                st.error(f"Preview error: {str(e)}")

if uploaded:
    # Choose processing mode
    if multichar_mode:
        st.subheader("🎭 Multi-Character Processing")
        if st.button("Start Multi-Character Dub", type="primary"):
            with st.spinner("Processing multi-character dubbing..."):
                try:
                    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                    r = requests.post(API_BASE + "/api/multichar/dub/video", files=files, timeout=600)
                    
                    if r.status_code == 200:
                        result = r.json()
                        st.success("✅ Multi-character dubbing completed!")
                        
                        # Display results
                        if "statistics" in result:
                            stats = result["statistics"]
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Speakers", stats.get("speakers", {}).get("total_speakers", 0))
                            with col2:
                                st.metric("Segments", stats.get("segments_processed", 0))
                            with col3:
                                st.metric("Profiles", stats.get("profiles", {}).get("total_speakers", 0))
                        
                        # Show emotion distribution
                        if "emotions" in result.get("statistics", {}):
                            emotions = result["statistics"]["emotions"]
                            st.subheader("Emotion Distribution")
                            emotion_data = []
                            for emotion, data in emotions.get("emotion_distribution", {}).items():
                                emotion_data.append({
                                    "Emotion": emotion,
                                    "Count": data.get("count", 0),
                                    "Avg Confidence": f"{data.get('average_confidence', 0):.2f}"
                                })
                            if emotion_data:
                                st.dataframe(emotion_data)
                        
                        # Download link
                        if "output" in result:
                            st.download_button(
                                label="📥 Download Multi-Character Dub",
                                data=b"Mock video data",  # In real implementation, this would be the actual video
                                file_name=f"multidub_{uploaded.name}",
                                mime="video/mp4"
                            )
                    else:
                        st.error(f"❌ Multi-character dubbing failed: {r.text}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        # Original single-character processing
        st.subheader("🎬 Single-Character Processing")
        
        # Processing parameters
        params = {
            "target_language": target_language,
            "voice_id": voice_id,
            "emotion": emotion,
            "tone": tone,
            "lip_sync_model": lip_sync_model,
            "quality_mode": quality_mode,
            "enable_realtime": enable_realtime
        }
        
        # Prepare file data
        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
        
        if enable_realtime:
        # Real-time processing
        st.info("🚀 Starting real-time processing...")
        
        # Create placeholder for real-time updates
        progress_bar = st.progress(0)
        status_text = st.empty()
        quality_metrics = st.empty()
        
        try:
            # Start processing
            response = requests.post(
                API_BASE + "/api/dub/video", 
                files=files, 
                params=params,
                timeout=1200
            )
            
            result = response.json()
            
            if result.get("status") == "processing_realtime":
                session_id = result["session_id"]
                websocket_url = result["websocket_url"]
                
                st.success(f"✅ Processing started! Session ID: {session_id}")
                st.info(f"WebSocket URL: {websocket_url}")
                
                # Simulate real-time updates (in a real implementation, 
                # this would connect to the WebSocket)
                for i in range(10):
                    progress = (i + 1) / 10
                    progress_bar.progress(progress)
                    
                    stages = [
                        "Initializing...",
                        "Extracting audio...",
                        "Transcribing...",
                        "Translating...",
                        "Synthesizing voice...",
                        "Lip-syncing...",
                        "Composing final video...",
                        "Quality assessment...",
                        "Finalizing...",
                        "Completed!"
                    ]
                    
                    status_text.text(f"Stage {i+1}/10: {stages[i]}")
                    
                    # Simulate quality metrics
                    if i >= 7:
                        quality_metrics.metric("Quality Score", f"{0.85 + (i-7)*0.05:.2f}")
                    
                    time.sleep(0.5)
                
                st.success("🎉 Real-time processing completed!")
                
            else:
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                
        except requests.exceptions.Timeout:
            st.error("⏰ Processing timeout - try reducing quality or file size")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    else:
        # Standard processing
        st.info("🔄 Processing video with advanced AI features...")
        
        with st.spinner("Processing in progress..."):
            try:
                response = requests.post(
                    API_BASE + "/api/dub/video", 
                    files=files, 
                    params=params,
                    timeout=1200
                )
                
                result = response.json()
                
                if result.get("status") == "completed":
                    st.success("✅ Processing completed!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Quality Score", f"{result.get('quality_score', 0):.2f}")
                    
                    with col2:
                        st.metric("Processing Time", f"{result.get('processing_time', 0):.1f}s")
                    
                    with col3:
                        st.metric("Model Used", result.get('model_used', 'unknown'))
                    
                    # Quality level indicator
                    quality_level = result.get('quality_level', 'unknown')
                    quality_colors = {
                        'excellent': '🟢',
                        'good': '🟡', 
                        'fair': '🟠',
                        'poor': '🔴'
                    }
                    
                    st.info(f"Quality Level: {quality_colors.get(quality_level, '⚪')} {quality_level.title()}")
                    
                    # Download link (mock)
                    st.download_button(
                        label="📥 Download Dubbed Video",
                        data=b"Mock video data",  # In real implementation, this would be the actual video
                        file_name=f"dubbed_{uploaded.name}",
                        mime="video/mp4"
                    )
                    
                else:
                    st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Processing timeout - try reducing quality or file size")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# AI Features showcase
st.markdown("---")
st.header("🤖 AI Features Showcase")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎭 VibeVoice TTS")
    st.markdown("""
    - **Voice Cloning**: Create custom voices
    - **Emotion Control**: Happy, sad, excited, calm
    - **Anime Optimized**: Perfect for anime content
    - **Real-time Synthesis**: Fast processing
    """)

with col2:
    st.subheader("👄 Advanced Lip-Sync")
    st.markdown("""
    - **Multiple Models**: Wav2Lip, SadTalker, Real-ESRGAN
    - **Quality Assessment**: Automatic quality scoring
    - **Anime Support**: Optimized for anime characters
    - **Batch Processing**: Handle multiple videos
    """)

with col3:
    st.subheader("⚡ Real-time Processing")
    st.markdown("""
    - **Live Updates**: WebSocket streaming
    - **Progressive Preview**: See results as they process
    - **Chunked Processing**: Handle large files
    - **Error Recovery**: Automatic retry mechanisms
    """)

# System status with AI features
st.markdown("---")
st.header("🔧 AI System Status")

ai_status_col1, ai_status_col2 = st.columns(2)

with ai_status_col1:
    st.subheader("TTS Models")
    tts_status = {
        "VibeVoice": "🟢 Active",
        "ElevenLabs": "🟡 Fallback", 
        "Mock TTS": "🟢 Available"
    }
    
    for model, status in tts_status.items():
        st.text(f"{model}: {status}")

with ai_status_col2:
    st.subheader("Lip-Sync Models")
    lipsync_status = {
        "Wav2Lip": "🟢 Available",
        "SadTalker": "🟡 GPU Required",
        "Real-ESRGAN": "🔴 Not Installed",
        "Mock Mode": "🟢 Always Available"
    }
    
    for model, status in lipsync_status.items():
        st.text(f"{model}: {status}")

# Performance Dashboard
st.markdown("---")
st.header("📊 Performance Dashboard")

# Create tabs for different performance views
tab1, tab2, tab3, tab4 = st.tabs(["Latency & Throughput", "Resource Usage", "Quality Metrics", "Error Logs"])

# Reports directory
REPORTS_DIR = Path("reports")
LOGS_DIR = Path("logs")

with tab1:
    st.subheader("Latency & Throughput")
    
    # Load latest metrics
    metrics_file = REPORTS_DIR / "system_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            if "summary" in metrics_data and "endpoint_stats" in metrics_data["summary"]:
                endpoint_stats = metrics_data["summary"]["endpoint_stats"]
                
                if endpoint_stats and PLOTLY_AVAILABLE:
                    # Create latency bar chart
                    endpoints = list(endpoint_stats.keys())
                    avg_latencies = [stats["avg_latency"] for stats in endpoint_stats.values()]
                    
                    fig = go.Figure(data=[
                        go.Bar(x=endpoints, y=avg_latencies, marker_color='lightblue')
                    ])
                    fig.update_layout(
                        title="Average Latency by Endpoint",
                        xaxis_title="Endpoint",
                        yaxis_title="Latency (seconds)",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display table
                    df = pd.DataFrame([
                        {"Endpoint": name, "Avg Latency (s)": stats["avg_latency"], "Count": stats["count"]}
                        for name, stats in endpoint_stats.items()
                    ])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No endpoint statistics available")
            else:
                st.info("No metrics data available. Run benchmark to generate data.")
        except Exception as e:
            st.error(f"Error loading metrics: {e}")
    else:
        st.info("No metrics file found. Run `python sonora/scripts/benchmark_system_performance.py` to generate performance data.")
    
    # Latency histogram image
    latency_img = REPORTS_DIR / "latency_histogram.png"
    if latency_img.exists() and PIL_AVAILABLE:
        st.subheader("Latency Distribution")
        img = Image.open(latency_img)
        st.image(img, use_container_width=True)

with tab2:
    st.subheader("Resource Usage")
    
    metrics_file = REPORTS_DIR / "system_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            summary = metrics_data.get("summary", {})
            
            # Display resource metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg CPU", f"{summary.get('avg_cpu_percent', 0):.1f}%")
            with col2:
                st.metric("Peak CPU", f"{summary.get('max_cpu_percent', 0):.1f}%")
            with col3:
                st.metric("Avg Memory", f"{summary.get('avg_memory_percent', 0):.1f}%")
            with col4:
                st.metric("Peak Memory", f"{summary.get('max_memory_percent', 0):.1f}%")
            
            # GPU usage chart
            gpu_html = REPORTS_DIR / "gpu_usage.html"
            if gpu_html.exists():
                with open(gpu_html, 'r') as f:
                    st.components.v1.html(f.read(), height=400)
            else:
                st.info("GPU usage chart not available. Run benchmark to generate.")
            
            # Memory timeline
            memory_html = REPORTS_DIR / "memory_timeline.html"
            if memory_html.exists():
                with open(memory_html, 'r') as f:
                    st.components.v1.html(f.read(), height=400)
            else:
                st.info("Memory timeline not available. Run benchmark to generate.")
                
        except Exception as e:
            st.error(f"Error loading resource data: {e}")
    else:
        st.info("No metrics file found. Run benchmark to generate resource usage data.")

with tab3:
    st.subheader("Quality Metrics")
    
    metrics_file = REPORTS_DIR / "system_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            # Quality correlation chart
            quality_html = REPORTS_DIR / "quality_correlation.html"
            if quality_html.exists():
                with open(quality_html, 'r') as f:
                    st.components.v1.html(f.read(), height=400)
            else:
                st.info("Quality correlation chart not available.")
            
            # Display quality scores
            if "results" in metrics_data:
                results = metrics_data["results"]
                quality_data = []
                
                for result in results:
                    if result.get("success"):
                        quality_data.append({
                            "Endpoint": result.get("name", "Unknown"),
                            "Latency (s)": result.get("latency", 0),
                            "Processing Time (s)": result.get("processing_time", 0),
                            "Status": "✅ Success"
                        })
                
                if quality_data:
                    df = pd.DataFrame(quality_data)
                    st.dataframe(df, use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error loading quality metrics: {e}")
    else:
        st.info("No metrics file found. Run benchmark to generate quality metrics.")
    
    # Performance summary
    summary_file = REPORTS_DIR / "performance_summary.md"
    if summary_file.exists():
        with st.expander("📄 View Performance Summary Report"):
            with open(summary_file, 'r') as f:
                st.markdown(f.read())

with tab4:
    st.subheader("Error Logs")
    
    log_file = LOGS_DIR / "test_results.log"
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
            
            # Show last 50 lines
            st.text_area("Recent Log Entries", "\n".join(log_lines[-50:]), height=400)
            
            # Download log button
            with open(log_file, 'r') as f:
                st.download_button(
                    label="📥 Download Full Log",
                    data=f.read(),
                    file_name="test_results.log",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"Error reading log file: {e}")
    else:
        st.info("No log file found. Logs will be created when tests are run.")
    
    # Error statistics
    metrics_file = REPORTS_DIR / "system_metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            summary = metrics_data.get("summary", {})
            total_tests = summary.get("total_tests", 0)
            failed_tests = summary.get("failed_tests", 0)
            success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Tests", total_tests)
            with col2:
                st.metric("Success Rate", f"{success_rate:.1f}%")
                
        except Exception as e:
            st.error(f"Error loading error statistics: {e}")

# Auto-refresh toggle
st.sidebar.markdown("---")
st.sidebar.header("Performance Dashboard")
auto_refresh_perf = st.sidebar.checkbox("Auto-refresh Performance Data", value=False)

if auto_refresh_perf:
    time.sleep(5)
    st.rerun()

# Manual refresh button
if st.sidebar.button("🔄 Refresh Performance Data"):
    st.cache_data.clear()
    st.rerun()

# Run benchmark button
if st.sidebar.button("🚀 Run Performance Benchmark"):
    st.sidebar.info("Starting benchmark... Check terminal for progress.")
    import subprocess
    import sys
    try:
        # Run benchmark in background
        benchmark_path = Path("sonora/scripts/benchmark_system_performance.py")
        if benchmark_path.exists():
            subprocess.Popen([
                sys.executable,
                str(benchmark_path)
            ])
            st.sidebar.success("Benchmark started! Check back in a few minutes.")
        else:
            st.sidebar.error("Benchmark script not found")
    except Exception as e:
        st.sidebar.error(f"Failed to start benchmark: {e}")
