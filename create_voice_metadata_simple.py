import os, csv, json, soundfile as sf
from glob import glob
from pathlib import Path
from tqdm import tqdm

out_dir = "./output"
os.makedirs(out_dir, exist_ok=True)
csv_path = os.path.join(out_dir, "metadata_unified.csv")
json_path = os.path.join(out_dir, "metadata_summary.json")

rows = []

def detect_emotion(name):
    for emo in ["ANG", "DIS", "FEA", "HAP", "NEU", "SAD", "SUR", "calm", "happy", "sad", "angry", "fear", "disgust", "neutral"]:
        if emo.lower() in name.lower(): 
            return emo.upper()
    return ""

def detect_language(dataset):
    if "libri" in dataset: 
        return "English"
    if "jvs" in dataset: 
        return "Japanese"
    return "English"

def parse_transcript(path):
    txt_file = os.path.splitext(path)[0] + ".txt"
    if os.path.exists(txt_file):
        try:
            return open(txt_file, "r", encoding="utf-8").read().strip()
        except: 
            pass
    return ""

for dataset_dir in os.listdir("./data"):
    ds_path = os.path.join("./data", dataset_dir)
    if not os.path.isdir(ds_path): 
        continue
    print(f"Scanning {dataset_dir}...")
    
    # Search for all audio formats
    audio_extensions = ['.wav', '.flac', '.mp3', '.m4a']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(glob(os.path.join(ds_path, "**", f"*{ext}"), recursive=True))
    
    print(f"  Found {len(audio_files)} audio files")
    
    # Process with progress bar for large datasets
    for audio_path in tqdm(audio_files, desc=f"  Processing {dataset_dir}", leave=False):
        try:
            # Use soundfile for WAV/FLAC, librosa for MP3/M4A
            audio_ext = os.path.splitext(audio_path)[1].lower()
            if audio_ext in ['.wav', '.flac']:
                info = sf.info(audio_path)
                duration = round(info.duration, 2)
                sample_rate = info.samplerate
            else:
                # Use librosa for MP3/M4A (handles more formats)
                try:
                    import librosa
                    y, sr = librosa.load(audio_path, sr=None, duration=300)  # Limit to 5min for speed
                    duration = round(librosa.get_duration(y=y, sr=sr), 2)
                    sample_rate = sr
                except ImportError:
                    # Fallback: try soundfile anyway
                    info = sf.info(audio_path)
                    duration = round(info.duration, 2)
                    sample_rate = info.samplerate
            
            transcript = parse_transcript(audio_path)
            emotion = detect_emotion(os.path.basename(audio_path))
            lang = detect_language(dataset_dir)
            
            # Extract speaker ID from filename
            basename = os.path.basename(audio_path)
            speaker_id = basename.split("_")[0] if "_" in basename else "unknown"
            
            rows.append({
                "audio_path": audio_path,
                "transcript": transcript,
                "speaker_id": speaker_id,
                "emotion_label": emotion,
                "language": lang,
                "dataset_source": dataset_dir,
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": "",
            })
        except Exception as e:
            print(f"Error on {audio_path}: {e}")

# --- WRITE OUTPUT ---
fieldnames = ["audio_path","transcript","speaker_id","emotion_label","language","dataset_source","duration","sample_rate","notes"]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    if rows:
        writer.writerows(rows)

summary = {
    "total_files": len(rows),
    "datasets": [d for d in os.listdir("./data") if os.path.isdir(os.path.join("./data", d))],
    "status": "completed" if rows else "no audio found"
}

json.dump(summary, open(json_path, "w", encoding="utf-8"), indent=2)

print(f"\n✅ Metadata written: {csv_path}")
print(f"✅ Summary: {json_path}")
print(f"📊 Total files processed: {len(rows)}")

