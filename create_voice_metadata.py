"""
🎧 SONORA VOICE METADATA CREATION SCRIPT
========================================

Creates unified metadata for expressive voice datasets (CREMA-D, JVS, RAVDESS, LibriSpeech, EmoV-DB, Expresso)
for fine-tuning VibeVoice or AutoTrain pipelines.

Usage:
    python create_voice_metadata.py [--data-dir /path/to/data] [--output-dir /path/to/output]
"""

import os
import json
import argparse
import pandas as pd
import librosa
from tqdm import tqdm
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore', category=UserWarning)


# ===========================================
# CONFIGURATION
# ===========================================

# Standard emotion mapping
EMOTION_MAP = {
    # CREMA-D
    "HAP": "happy", "HAPPY": "happy", "H": "happy",
    "SAD": "sad", "S": "sad",
    "ANG": "angry", "ANGRY": "angry", "A": "angry",
    "FEA": "fearful", "FEAR": "fearful", "FEARFUL": "fearful", "F": "fearful",
    "DIS": "disgust", "DISGUST": "disgust", "D": "disgust",
    "NEU": "neutral", "NEUTRAL": "neutral", "N": "neutral",
    "CAL": "calm", "CALM": "calm", "C": "calm",
    "SUR": "surprise", "SURPRISE": "surprise", "SU": "surprise",
    "OTH": "other", "OTHER": "other", "O": "other",
    
    # RAVDESS
    "01": "neutral", "02": "calm", "03": "happy", "04": "sad",
    "05": "angry", "06": "fearful", "07": "disgust", "08": "surprise",
    
    # EmoV-DB
    "amusement": "happy", "excitement": "happy",
    "sadness": "sad", "anger": "angry", "fear": "fearful",
    "disgust": "disgust", "neutral": "neutral",
    
    # JVS styles (mapped to emotions where applicable)
    "normal": "neutral", "whisper": "neutral", "falsetto": "other",
    "reading": "neutral", "emotion": "other",
}

STANDARD_EMOTIONS = ["neutral", "happy", "sad", "angry", "fearful", "disgust", "surprise", "calm", "other"]


# ===========================================
# DATASET EXTRACTORS
# ===========================================

class MetadataExtractor:
    """Base class for dataset-specific metadata extraction."""
    
    def __init__(self, base_dir: str, dataset_name: str):
        self.base_dir = Path(base_dir)
        self.dataset_name = dataset_name
        self.metadata_rows: List[Dict] = []
    
    def normalize_emotion(self, emotion: str) -> str:
        """Normalize emotion to standard set."""
        if not emotion:
            return "other"
        emotion_upper = emotion.upper().strip()
        normalized = EMOTION_MAP.get(emotion_upper, emotion.lower().strip())
        # Ensure it's in standard set
        if normalized not in STANDARD_EMOTIONS:
            # Try fuzzy match
            for std_emotion in STANDARD_EMOTIONS:
                if std_emotion in normalized or normalized in std_emotion:
                    return std_emotion
            return "other"
        return normalized
    
    def get_audio_properties(self, audio_path: str) -> Tuple[Optional[float], Optional[int]]:
        """Get duration and sample rate from audio file."""
        try:
            y, sr = librosa.load(audio_path, sr=None, mono=True, duration=300)  # Limit to 5min for speed
            duration = round(librosa.get_duration(y=y, sr=sr), 2)
            return duration, sr
        except Exception as e:
            print(f"⚠️ Error loading {audio_path}: {e}")
            return None, None
    
    def extract(self) -> List[Dict]:
        """Main extraction method - override in subclasses."""
        raise NotImplementedError


class CREMADExtractor(MetadataExtractor):
    """CREMA-D dataset extractor.
    
    Filename format: {speaker_id}_{sentence}_{emotion}_{intensity}.wav
    Example: 1016_IEO_HAP_HI.wav
    """
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / "crema_d"
        if not path.exists():
            path = self.base_dir / "CREMA-D"
        if not path.exists():
            path = self.base_dir / "crema"
        if not path.exists():
            print(f"⚠️ Skipping CREMA-D, directory not found: {path}")
            return []
        
        print(f"🔍 Scanning CREMA-D...")
        audio_files = list(path.rglob("*.wav"))
        print(f"   Found {len(audio_files)} audio files")
        
        for audio_file in tqdm(audio_files, desc="   Processing"):
            filename = audio_file.stem  # Without extension
            parts = filename.split("_")
            
            if len(parts) >= 3:
                speaker_id = parts[0]
                # Emotion is typically in 3rd position
                emotion_code = parts[2][:3].upper() if len(parts[2]) >= 3 else parts[2].upper()
                emotion = self.normalize_emotion(emotion_code)
            else:
                speaker_id = "unknown"
                emotion = "other"
            
            duration, sample_rate = self.get_audio_properties(str(audio_file))
            
            self.metadata_rows.append({
                "audio_path": str(audio_file.resolve()),
                "transcript": None,
                "speaker_id": speaker_id,
                "emotion_label": emotion,
                "language": "en",
                "dataset_source": "crema_d",
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": None
            })
        
        return self.metadata_rows


class JVSExtractor(MetadataExtractor):
    """JVS (Japanese Voice Style) dataset extractor.
    
    Directory structure: jvs/{speaker}/parallel100/{style}/...wav
    Supports: jvs, jvs_ver1
    """
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / self.dataset_name
        if not path.exists():
            path = self.base_dir / "jvs"
        if not path.exists():
            path = self.base_dir / "jvs_ver1"
        if not path.exists():
            print(f"⚠️ Skipping JVS, directory not found: {path}")
            return []
        
        print(f"🔍 Scanning JVS...")
        audio_files = list(path.rglob("*.wav"))
        print(f"   Found {len(audio_files)} audio files")
        
        for audio_file in tqdm(audio_files, desc="   Processing"):
            # Extract speaker from path: jvs/{speaker}/...
            parts = audio_file.parts
            speaker_idx = -1
            for i, part in enumerate(parts):
                if part in ["jvs", "jvs_ver1"] and i + 1 < len(parts):
                    speaker_idx = i + 1
                    break
            
            speaker_id = parts[speaker_idx] if speaker_idx >= 0 else "unknown"
            
            # Try to extract style from directory name
            style = audio_file.parent.name
            emotion = self.normalize_emotion(style)
            
            duration, sample_rate = self.get_audio_properties(str(audio_file))
            
            self.metadata_rows.append({
                "audio_path": str(audio_file.resolve()),
                "transcript": None,
                "speaker_id": speaker_id,
                "emotion_label": emotion,
                "language": "ja",
                "dataset_source": "jvs",
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": style
            })
        
        return self.metadata_rows


class RAVDESSExtractor(MetadataExtractor):
    """RAVDESS (Ryerson Audio-Visual Database of Emotional Speech) extractor.
    
    Filename format: {modality}-{vocal_channel}-{emotion}-{emotional_intensity}-{statement}-{repetition}-{actor}.wav
    Example: 03-01-06-01-02-01-01.wav (Audio-Video, Channel 1, Fear, Normal intensity, Statement 2, Rep 1, Actor 1)
    Emotion codes: 01=neutral, 02=calm, 03=happy, 04=sad, 05=angry, 06=fearful, 07=disgust, 08=surprise
    Supports: ravdess, Audio_Speech_Actors_01-24
    """
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / "ravdess"
        if not path.exists():
            path = self.base_dir / "Audio_Speech_Actors_01-24"
        if not path.exists():
            print(f"⚠️ Skipping RAVDESS, directory not found: {path}")
            return []
        
        print(f"🔍 Scanning RAVDESS...")
        audio_files = list(path.rglob("*.wav"))
        print(f"   Found {len(audio_files)} audio files")
        
        for audio_file in tqdm(audio_files, desc="   Processing"):
            filename = audio_file.stem
            parts = filename.split("-")
            
            if len(parts) >= 7:
                emotion_code = parts[2]  # 3rd field is emotion
                speaker_id = parts[6]    # Last field is actor
                emotion = self.normalize_emotion(emotion_code)
            else:
                emotion_code = None
                speaker_id = "unknown"
                emotion = "other"
            
            duration, sample_rate = self.get_audio_properties(str(audio_file))
            
            self.metadata_rows.append({
                "audio_path": str(audio_file.resolve()),
                "transcript": None,
                "speaker_id": f"ravdess_{speaker_id}",
                "emotion_label": emotion,
                "language": "en",
                "dataset_source": "ravdess",
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": f"emotion_code={emotion_code}" if emotion_code else None
            })
        
        return self.metadata_rows


class LibriSpeechExtractor(MetadataExtractor):
    """LibriSpeech dataset extractor.
    
    Directory structure: librispeech/{split}/{speaker}/{chapter}/...wav
    Transcripts are in corresponding .txt files.
    """
    
    def find_transcript(self, audio_file: Path) -> Optional[str]:
        """Find corresponding transcript for audio file."""
        # LibriSpeech stores transcripts in .trans.txt files in the chapter directory
        chapter_dir = audio_file.parent
        transcript_file = chapter_dir / f"{chapter_dir.name}.trans.txt"
        
        # Also check for alternative transcript file names
        if not transcript_file.exists():
            transcript_file = chapter_dir / f"{audio_file.stem}.txt"
        if not transcript_file.exists():
            transcript_file = chapter_dir.parent / f"{chapter_dir.name}.trans.txt"
        
        if transcript_file.exists():
            # Transcript file format: {audio_id} {transcript}
            audio_id = audio_file.stem
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith(audio_id):
                            return line[len(audio_id):].strip()
            except Exception as e:
                print(f"⚠️ Error reading transcript {transcript_file}: {e}")
        
        return None
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / self.dataset_name
        if not path.exists():
            path = self.base_dir / "librispeech"
        if not path.exists():
            path = self.base_dir / "libri"
        if not path.exists():
            path = self.base_dir / "train-clean-100"
        if not path.exists():
            # Try to find any train-clean-* folder
            train_folders = list(self.base_dir.glob("train-clean-*"))
            if train_folders:
                path = train_folders[0]
        if not path.exists():
            print(f"⚠️ Skipping LibriSpeech, directory not found")
            return []
        
        print(f"🔍 Scanning LibriSpeech...")
        audio_files = list(path.rglob("*.flac"))  # LibriSpeech uses FLAC
        print(f"   Found {len(audio_files)} audio files")
        
        for audio_file in tqdm(audio_files, desc="   Processing"):
            # Extract speaker from path: librispeech/{split}/{speaker}/...
            parts = audio_file.parts
            speaker_id = "unknown"
            dataset_names = ["librispeech", "libri"]
            for i, part in enumerate(parts):
                if part in dataset_names or (i > 0 and parts[i-1] in ["train-clean", "train-other", "dev-clean", "dev-other", "test-clean", "test-other"]):
                    if i + 1 < len(parts):
                        speaker_id = parts[i + 1]
                        break
            
            transcript = self.find_transcript(audio_file)
            
            duration, sample_rate = self.get_audio_properties(str(audio_file))
            
            self.metadata_rows.append({
                "audio_path": str(audio_file.resolve()),
                "transcript": transcript,
                "speaker_id": f"librispeech_{speaker_id}",
                "emotion_label": "neutral",  # LibriSpeech is neutral reading
                "language": "en",
                "dataset_source": "librispeech",
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": None
            })
        
        return self.metadata_rows


class EmoVDBExtractor(MetadataExtractor):
    """EmoV-DB (Emotional Voices Database) extractor.
    
    May use JSON metadata or filename parsing for emotions.
    Supports: emovdb, emovdb_raw
    """
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / self.dataset_name
        if not path.exists():
            path = self.base_dir / "emovdb"
        if not path.exists():
            path = self.base_dir / "emovdb_raw"
        if not path.exists():
            print(f"⚠️ Skipping EmoV-DB, directory not found: {path}")
            return []
        
        print(f"🔍 Scanning EmoV-DB...")
        audio_files = list(path.rglob("*.wav"))
        
        # Try to find JSON metadata file
        json_files = list(path.rglob("*.json"))
        metadata_dict = {}
        
        if json_files:
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            metadata_dict.update(data)
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and "file" in item:
                                    metadata_dict[item["file"]] = item
                except Exception as e:
                    print(f"⚠️ Error reading JSON {json_file}: {e}")
        
        print(f"   Found {len(audio_files)} audio files")
        
        for audio_file in tqdm(audio_files, desc="   Processing"):
            filename = audio_file.name
            
            # Try to get metadata from JSON
            emotion = "neutral"
            speaker_id = "unknown"
            transcript = None
            
            if filename in metadata_dict:
                meta = metadata_dict[filename]
                emotion = self.normalize_emotion(meta.get("emotion", "neutral"))
                speaker_id = meta.get("speaker", "unknown")
                transcript = meta.get("transcript")
            else:
                # Fallback: parse filename
                # EmoV-DB filenames often contain emotion in lowercase
                filename_lower = filename.lower()
                for emo_key, emo_val in EMOTION_MAP.items():
                    if emo_key.lower() in filename_lower:
                        emotion = emo_val
                        break
                
                # Try to extract speaker from filename
                parts = filename.split("_")
                if len(parts) > 0:
                    speaker_id = parts[0]
            
            duration, sample_rate = self.get_audio_properties(str(audio_file))
            
            self.metadata_rows.append({
                "audio_path": str(audio_file.resolve()),
                "transcript": transcript,
                "speaker_id": f"emovdb_{speaker_id}",
                "emotion_label": emotion,
                "language": "en",
                "dataset_source": "emovdb",
                "duration": duration,
                "sample_rate": sample_rate,
                "notes": None
            })
        
        return self.metadata_rows


class ExpressoExtractor(MetadataExtractor):
    """Expresso dataset extractor.
    
    Uses parquet files for structured metadata.
    Supports: expresso, expresso_dataset
    """
    
    def extract(self) -> List[Dict]:
        # Try multiple possible folder names
        path = self.base_dir / "expresso"
        if not path.exists():
            path = self.base_dir / "expresso_dataset"
        if not path.exists():
            print(f"⚠️ Skipping Expresso, directory not found: {path}")
            return []
        
        print(f"🔍 Scanning Expresso...")
        
        # Look for parquet files
        parquet_files = list(path.rglob("*.parquet"))
        pyarrow_available = False
        
        if parquet_files:
            print(f"   Found {len(parquet_files)} parquet metadata files")
            # Check if pyarrow is available
            try:
                import pyarrow
                pyarrow_available = True
            except ImportError:
                print("   ⚠️ pyarrow not installed. Install with: pip install pyarrow")
                print("   Falling back to direct audio file scanning...")
            
            if pyarrow_available:
                for pq_file in parquet_files:
                    try:
                        df_pq = pd.read_parquet(pq_file)
                        print(f"   Processing {pq_file.name} with {len(df_pq)} entries")
                        
                        # Map parquet columns to our format
                        for _, row in df_pq.iterrows():
                            audio_path_col = None
                            for col in ["audio_path", "path", "file", "filepath", "audio"]:
                                if col in df_pq.columns:
                                    audio_path_col = col
                                    break
                            
                            if audio_path_col is None:
                                continue
                            
                            # Resolve audio file path
                            audio_rel_path = row[audio_path_col]
                            audio_file = path / audio_rel_path if not os.path.isabs(audio_rel_path) else Path(audio_rel_path)
                            
                            if not audio_file.exists():
                                # Try to find it
                                audio_file = path / Path(audio_rel_path).name
                                if not audio_file.exists():
                                    continue
                            
                            # Extract metadata from parquet
                            transcript = row.get("transcript") or row.get("text") or None
                            speaker_id = str(row.get("speaker_id") or row.get("speaker") or "unknown")
                            emotion_raw = row.get("emotion") or row.get("emotion_label") or "neutral"
                            emotion = self.normalize_emotion(str(emotion_raw))
                            language = row.get("language") or "en"
                            
                            duration, sample_rate = self.get_audio_properties(str(audio_file))
                            
                            self.metadata_rows.append({
                                "audio_path": str(audio_file.resolve()),
                                "transcript": transcript,
                                "speaker_id": f"expresso_{speaker_id}",
                                "emotion_label": emotion,
                                "language": language,
                                "dataset_source": "expresso",
                                "duration": duration,
                                "sample_rate": sample_rate,
                                "notes": None
                            })
                    except Exception as e:
                        print(f"⚠️ Error processing parquet {pq_file}: {e}")
        
        # Fallback to direct audio file scanning if no parquet or pyarrow unavailable
        if not parquet_files or not pyarrow_available:
            # Fallback: scan audio files directly
            audio_files = list(path.rglob("*.wav")) + list(path.rglob("*.flac"))
            print(f"   No parquet files found, scanning {len(audio_files)} audio files directly")
            
            for audio_file in tqdm(audio_files, desc="   Processing"):
                duration, sample_rate = self.get_audio_properties(str(audio_file))
                
                self.metadata_rows.append({
                    "audio_path": str(audio_file.resolve()),
                    "transcript": None,
                    "speaker_id": "unknown",
                    "emotion_label": "neutral",
                    "language": "en",
                    "dataset_source": "expresso",
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "notes": None
                })
        
        return self.metadata_rows


# ===========================================
# MAIN PROCESSING
# ===========================================

def create_metadata(data_dir: str, output_dir: str = None):
    """Main function to create unified metadata."""
    
    if output_dir is None:
        output_dir = os.getcwd()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🎧 SONORA VOICE METADATA CREATION")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Initialize extractors
    # Support multiple possible folder name variations
    extractors = {
        "crema_d": CREMADExtractor(data_dir, "crema_d"),
        "jvs": JVSExtractor(data_dir, "jvs"),
        "jvs_ver1": JVSExtractor(data_dir, "jvs_ver1"),
        "ravdess": RAVDESSExtractor(data_dir, "ravdess"),
        "Audio_Speech_Actors_01-24": RAVDESSExtractor(data_dir, "Audio_Speech_Actors_01-24"),
        "librispeech": LibriSpeechExtractor(data_dir, "librispeech"),
        "libri": LibriSpeechExtractor(data_dir, "libri"),
        "train-clean-100": LibriSpeechExtractor(data_dir, "train-clean-100"),
        "emovdb": EmoVDBExtractor(data_dir, "emovdb"),
        "emovdb_raw": EmoVDBExtractor(data_dir, "emovdb_raw"),
        "expresso": ExpressoExtractor(data_dir, "expresso"),
        "expresso_dataset": ExpressoExtractor(data_dir, "expresso_dataset"),
    }
    
    all_metadata = []
    
    # Extract from each dataset
    processed_datasets = set()
    for name, extractor in extractors.items():
        # Skip duplicate processing for alternative folder names
        # Only process if we haven't found files for the base name
        if name == "jvs_ver1" and "jvs" in processed_datasets:
            continue
        if name == "libri" and "librispeech" in processed_datasets:
            continue
        if name == "emovdb_raw" and "emovdb" in processed_datasets:
            continue
        
        try:
            rows = extractor.extract()
            if rows:  # Only record if we found files
                all_metadata.extend(rows)
                print(f"✅ {name}: {len(rows)} files processed\n")
                processed_datasets.add(name)
                # Also mark base name as processed
                if name == "jvs_ver1":
                    processed_datasets.add("jvs")
                elif name == "libri":
                    processed_datasets.add("librispeech")
                elif name == "emovdb_raw":
                    processed_datasets.add("emovdb")
        except Exception as e:
            print(f"❌ Error processing {name}: {e}\n")
            continue
    
    if not all_metadata:
        print("❌ No metadata extracted! Check data directory paths.")
        return
    
    # Create DataFrame
    print(f"📊 Creating unified metadata DataFrame...")
    df = pd.DataFrame(all_metadata)
    
    # Ensure all required columns exist
    required_columns = ["audio_path", "transcript", "speaker_id", "emotion_label", 
                       "language", "dataset_source", "duration", "sample_rate", "notes"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    
    # Remove rows with invalid audio paths
    initial_count = len(df)
    df = df[df["audio_path"].notna()].copy()
    if len(df) < initial_count:
        print(f"⚠️ Removed {initial_count - len(df)} rows with invalid audio paths")
    
    # Create summary statistics
    print("📈 Computing summary statistics...")
    
    valid_durations = df["duration"].dropna()
    total_hours = round(valid_durations.sum() / 3600, 2) if len(valid_durations) > 0 else 0.0
    avg_duration = round(valid_durations.mean(), 2) if len(valid_durations) > 0 else 0.0
    
    summary = {
        "total_files": int(len(df)),
        "total_hours": total_hours,
        "total_minutes": round(total_hours * 60, 2),
        "average_duration_seconds": avg_duration,
        "languages": df["language"].value_counts().to_dict(),
        "datasets": df["dataset_source"].value_counts().to_dict(),
        "emotions": df["emotion_label"].value_counts().to_dict(),
        "speakers_count": int(df["speaker_id"].nunique()),
        "transcripts_available": int(df["transcript"].notna().sum()),
        "transcripts_percentage": round(df["transcript"].notna().sum() / len(df) * 100, 2),
    }
    
    # Export CSV
    csv_path = output_dir / "metadata_unified.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ Exported CSV: {csv_path}")
    
    # Export JSON summary
    json_path = output_dir / "metadata_summary.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported summary: {json_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 METADATA SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    
    # Print emotion distribution
    print("🎭 EMOTION DISTRIBUTION:")
    print("-" * 60)
    emotion_counts = df["emotion_label"].value_counts().sort_index()
    for emotion, count in emotion_counts.items():
        percentage = round(count / len(df) * 100, 1)
        print(f"  {emotion:15} {count:6} files ({percentage:5.1f}%)")
    print()
    
    # Print dataset distribution
    print("📚 DATASET DISTRIBUTION:")
    print("-" * 60)
    dataset_counts = df["dataset_source"].value_counts()
    for dataset, count in dataset_counts.items():
        percentage = round(count / len(df) * 100, 1)
        print(f"  {dataset:15} {count:6} files ({percentage:5.1f}%)")
    print()
    
    print("=" * 60)
    print("🎯 Metadata creation complete! Ready for fine-tuning.")
    print(f"   Metadata CSV: {csv_path}")
    print(f"   Summary JSON: {json_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Create unified voice metadata for Sonora fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_voice_metadata.py --data-dir ./data
  python create_voice_metadata.py --data-dir /content/data --output-dir ./output
        """
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Base directory containing dataset folders (default: ./data)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for metadata files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    create_metadata(args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()

