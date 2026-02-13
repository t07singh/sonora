import streamlit as st
import requests
import json

st.set_page_config(page_title="Sonora AI Interface (Mock)", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🎧 Sonora Voice & Sound Playground")
st.caption("Local mock version — connected to FastAPI backend")

tabs = st.tabs([
    "🎙️ Speech Recognition (ASR)",
    "🔊 Text to Speech (TTS)",
    "🌐 Translation",
    "🎚️ Voice Clone",
    "🎛️ Audio Sync & Align",
    "🧠 Model Inspector"
])

# ---- ASR ----
with tabs[0]:
    st.subheader("Speech Recognition (ASR)")
    audio_file = st.file_uploader("Upload audio for transcription", type=["wav", "mp3", "m4a"])
    if st.button("Run ASR"):
        if audio_file:
            files = {"file": audio_file.getvalue()}
            res = requests.post(f"{API_URL}/asr", files=files)
            st.json(res.json())
        else:
            st.warning("Please upload an audio file first.")

# ---- TTS ----
with tabs[1]:
    st.subheader("Text to Speech (TTS)")
    text = st.text_area("Enter text to generate speech")
    if st.button("Run TTS"):
        if text.strip():
            res = requests.post(f"{API_URL}/tts", json={"text": text})
            data = res.json()
            st.audio(data.get("audio_url", ""), format="audio/wav")
            st.json(data)
        else:
            st.warning("Please enter text first.")

# ---- Translation ----
with tabs[2]:
    st.subheader("Translation")
    text = st.text_area("Enter text to translate")
    target_lang = st.selectbox("Target language", ["en", "ja", "ko", "hi", "fr", "es"])
    if st.button("Run Translation"):
        res = requests.post(f"{API_URL}/translate", json={"text": text, "lang": target_lang})
        st.json(res.json())

# ---- Voice Clone ----
with tabs[3]:
    st.subheader("Voice Cloning")
    voice_sample = st.file_uploader("Upload sample voice", type=["wav", "mp3"])
    clone_text = st.text_area("Enter text to synthesize in cloned voice")
    if st.button("Clone Voice"):
        if voice_sample and clone_text:
            files = {"file": voice_sample.getvalue()}
            res = requests.post(f"{API_URL}/clone", files=files, data={"text": clone_text})
            st.audio(res.content, format="audio/wav")
        else:
            st.warning("Upload sample and enter text first.")

# ---- Audio Sync ----
with tabs[4]:
    st.subheader("Audio Sync / Alignment")
    transcript = st.text_area("Enter or paste transcript")
    audio_file = st.file_uploader("Upload reference audio", type=["wav", "mp3"])
    if st.button("Run Sync"):
        if transcript and audio_file:
            files = {"file": audio_file.getvalue()}
            res = requests.post(f"{API_URL}/align", files=files, data={"text": transcript})
            st.json(res.json())
        else:
            st.warning("Need both transcript and audio.")

# ---- Model Inspector ----
with tabs[5]:
    st.subheader("Inspect Available Models")
    res = requests.get(f"{API_URL}/models")
    if res.ok:
        data = res.json()
        st.success(f"Connected to backend: {API_URL}")
        st.json(data)
    else:
        st.error("Cannot connect to backend. Make sure FastAPI server is running at 127.0.0.1:8000.")
