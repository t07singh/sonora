
"""
SONORA EXECUTION: ITEM 2 - THE EMOTION TOKENIZER
Builds: Acoustic Feature Extraction + Wav2Vec2 Emotion Classification
"""
import librosa
import numpy as np
import torch
import warnings
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification

# Suppress some common warnings from librosa/transformers for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

class EmotionTokenizer:
    def __init__(self):
        # Using a professional-grade SER model (Speech Emotion Recognition)
        self.model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        print(f"Loading Emotion Model: {self.model_name}...")
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(self.model_name)
        self.emotions = ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"]
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Model loaded on {self.device}")

    def analyze_segment(self, audio_path):
        """Extracts both raw prosody and high-level emotion tokens."""
        # Standardize to 16kHz as expected by Wav2Vec2
        y, sr = librosa.load(audio_path, sr=16000)
        
        # 1. Acoustic Prosody (F0 and Energy)
        # Using pyin for robust pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'),
            sr=sr
        )
        energy = librosa.feature.rms(y=y)[0]
        
        # 2. AI Emotion Classification
        inputs = self.feature_extractor(y, sampling_rate=16000, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            logits = self.model(**inputs).logits
        
        scores = torch.nn.functional.softmax(logits, dim=-1)
        best_emotion_idx = torch.argmax(scores).item()
        
        return {
            "token": self.emotions[best_emotion_idx],
            "confidence": float(scores[0][best_emotion_idx].cpu()),
            "avg_pitch": float(np.nanmean(f0)) if not np.all(np.isnan(f0)) else 0.0,
            "intensity": float(np.mean(energy))
        }

    def get_director_cues(self, audio_path):
        """Generates a text description of the prosody for the LLM/TTS."""
        stats = self.analyze_segment(audio_path)
        token = stats['token']
        pitch = stats['avg_pitch']
        intensity = stats['intensity']
        
        # Heuristic mapping
        style = "Normal"
        if pitch > 200: style = "High-pitched"
        if pitch < 100: style = "Deep/Low"
        
        cues = f"Emotion: {token.upper()} (Confidence: {stats['confidence']:.2f}). "
        cues += f"Acoustics: {style} tone, Intensity level {intensity:.3f}. "
        cues += "Constraint: Match this energy."
        return cues

# --- TEST LOGIC ---
if __name__ == "__main__":
    try:
        tokenizer = EmotionTokenizer()
        print("DONE: Emotion Model Loaded")
        print("DONE: Prosody Engine Ready") 
        # Mock test
        print(f"Director Cue Test: {tokenizer.get_director_cues('sonora/data/sample.wav') if os.path.exists('sonora/data/sample.wav') else 'No File'}")
    except Exception as e:
        print(f"FAILED: {e}")
