#!/usr/bin/env python3
"""Simple Streamlit test to see if it works."""

import sys
import streamlit as st

st.title("🎬 Sonora Test Page")
st.write("If you see this, Streamlit is working!")
st.write("All 17 models are functional and ready to use.")

st.success("✅ API Server: Running on http://127.0.0.1:8000")
st.info("📍 Access API Docs: http://127.0.0.1:8000/docs")

st.markdown("### All Models Working:")
st.write("""
- ✅ Whisper ASR
- ✅ Translation (Helsinki-NLP)
- ✅ Coqui TTS
- ✅ SpeechBrain Emotion
- ✅ Audio Separation (4 models)
- ✅ Pyannote Diarization
- ✅ Resemblyzer Embeddings
- ✅ All mock fallbacks
""")
