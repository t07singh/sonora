# 🎬 Sonora Video Dubbing System

This document describes the video dubbing capabilities added to Sonora/Auralis AI Dubbing System, enabling full video processing with lip-synchronization.

## 🏗️ Architecture Overview

The video dubbing system follows a modular architecture with the following components:

```
[ VideoProcessor ]
       ↓
 ┌─────────────────────────────┐
 │   AudioExtractor (FFmpeg)   │
 └─────────────────────────────┘
       ↓
 ┌─────────────────────────────┐
 │     Sonora Core Pipeline    │  (ASR→GPT→TTS)
 └─────────────────────────────┘
       ↓
 ┌─────────────────────────────┐
 │   LipSyncEngine (Wav2Lip)   │
 └─────────────────────────────┘
       ↓
 ┌─────────────────────────────┐
 │   VideoComposer (FFmpeg)    │
 └─────────────────────────────┘
       ↓
     Final Output Video
```

## 📁 File Structure

```
sonora/
├── video_sync/                 # NEW: Video synchronization module
│   ├── __init__.py
│   ├── extractor.py           # FFmpeg audio extraction
│   ├── lipsync.py             # Wav2Lip / SadTalker wrapper
│   ├── composer.py            # Merge video + dubbed audio
│   └── utils.py               # Frame/audio helpers
├── api/
│   └── routes_video.py        # /api/dub/video endpoint
├── ui/
│   └── video_demo.py          # Streamlit video uploader/player
├── tests/
│   └── test_video_sync.py     # Video processing tests
└── run_video_demo.py          # Standalone demo script
```

## 🚀 Features

### Core Capabilities
- **Video Input Support**: Accept MP4, MOV, AVI, MKV, WebM files
- **Audio Extraction**: Extract audio tracks using FFmpeg
- **Lip-Synchronization**: Apply lip-sync using vision models (Wav2Lip, SadTalker)
- **Video Composition**: Merge dubbed audio with original video
- **Quality Assessment**: Evaluate lip-sync quality metrics

### Supported Formats
- **Video**: MP4, MOV, AVI, MKV, WebM, FLV, WMV
- **Audio**: WAV, MP3, M4A, AAC
- **Lip-Sync Models**: Mock, Wav2Lip, SadTalker

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- FFmpeg installed on system
- Required Python packages (see requirements.txt)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### System Requirements
- **FFmpeg**: Required for video/audio processing
- **OpenCV**: For video frame processing
- **CUDA**: Optional, for GPU acceleration of lip-sync models

## 📖 Usage

### 1. API Endpoints

#### Video Dubbing Endpoint
```bash
POST /api/dub/video
```

**Parameters:**
- `file`: Video file (multipart/form-data)
- `lip_sync_model`: "mock", "wav2lip", "sadtalker"
- `quality`: "low", "medium", "high"
- `include_subtitles`: boolean

**Example:**
```bash
curl -X POST "http://localhost:8000/api/dub/video" \
  -F "file=@input_video.mp4" \
  -F "lip_sync_model=mock" \
  -F "quality=medium" \
  -F "include_subtitles=false"
```

#### Get Supported Formats
```bash
GET /api/dub/video/formats
```

#### Get Component Status
```bash
GET /api/dub/video/status
```

### 2. Python API

```python
from sonora.video_sync.extractor import AudioExtractor
from sonora.video_sync.lipsync import LipSyncEngine
from sonora.video_sync.composer import VideoComposer

# Initialize components
extractor = AudioExtractor()
lip_sync = LipSyncEngine(model_type="mock")
composer = VideoComposer()

# Extract audio from video
audio_path = extractor.extract_audio("input_video.mp4")

# Run dubbing pipeline (ASR → Translation → TTS)
# ... (use existing Sonora pipeline)

# Apply lip-synchronization
lip_synced_path = lip_sync.sync_lips("input_video.mp4", "dubbed_audio.wav", "lip_synced.mp4")

# Compose final video
final_path = composer.compose_final_video(
    "input_video.mp4", 
    "dubbed_audio.wav", 
    lip_synced_path, 
    "final_output.mp4"
)
```

### 3. Streamlit Web UI

Launch the video dubbing web interface:

```bash
streamlit run sonora/ui/video_demo.py
```

Features:
- Drag-and-drop video upload
- Real-time processing status
- Video preview and download
- Configuration options

### 4. Demo Script

Run the standalone demo:

```bash
python sonora/run_video_demo.py
```

This creates a sample video, runs the complete pipeline, and shows the results.

## 🔧 Configuration

### Environment Variables
```bash
# API Keys (same as audio dubbing)
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Video Processing
FFMPEG_PATH=/usr/bin/ffmpeg  # Optional, auto-detected
CUDA_VISIBLE_DEVICES=0       # For GPU acceleration
```

### Lip-Sync Model Configuration

#### Mock Model (Default)
- Fast processing
- Simple audio replacement
- Good for testing

#### Wav2Lip Model
```python
lip_sync = LipSyncEngine(model_type="wav2lip", model_path="/path/to/wav2lip")
```

#### SadTalker Model
```python
lip_sync = LipSyncEngine(model_type="sadtalker", model_path="/path/to/sadtalker")
```

## 🧪 Testing

Run the video processing tests:

```bash
# Run all video sync tests
pytest sonora/tests/test_video_sync.py -v

# Run specific test class
pytest sonora/tests/test_video_sync.py::TestAudioExtractor -v

# Run integration tests
pytest sonora/tests/test_video_sync.py::TestVideoSyncIntegration -v
```

## 📊 Performance

### Processing Times (Approximate)
- **Audio Extraction**: 1-2 seconds per minute of video
- **ASR + Translation**: 5-10 seconds per minute of audio
- **TTS Generation**: 2-5 seconds per minute of audio
- **Lip-Sync (Mock)**: 2-5 seconds per minute of video
- **Lip-Sync (Wav2Lip)**: 30-60 seconds per minute of video
- **Video Composition**: 5-15 seconds per minute of video

### Quality Settings
- **Low**: Faster processing, lower quality
- **Medium**: Balanced speed and quality (recommended)
- **High**: Slower processing, highest quality

## 🐛 Troubleshooting

### Common Issues

#### FFmpeg Not Found
```bash
# Install FFmpeg
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

#### CUDA/GPU Issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Issues
- Reduce video resolution
- Use lower quality settings
- Process shorter video segments
- Increase system RAM

### Debug Mode
Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

### Planned Features
- **Real-time Processing**: Live video dubbing
- **Batch Processing**: Multiple video processing
- **Advanced Lip-Sync**: More sophisticated models
- **Subtitle Integration**: Automatic subtitle generation
- **Voice Cloning**: Custom voice profiles
- **Multi-language Support**: More language pairs

### Model Integration
- **Wav2Lip**: Full implementation
- **SadTalker**: Complete integration
- **First Order Motion**: Alternative lip-sync approach
- **Real-ESRGAN**: Video upscaling

## 📝 API Reference

### AudioExtractor
```python
class AudioExtractor:
    def extract_audio(video_path: str, out_audio: str = None) -> str
    def get_video_info(video_path: str) -> Dict[str, Any]
    def validate_video_file(video_path: str) -> bool
```

### LipSyncEngine
```python
class LipSyncEngine:
    def __init__(model_type: str = "mock", model_path: str = None)
    def sync_lips(video_path: str, audio_path: str, output_path: str) -> str
    def extract_face_region(video_path: str, output_dir: str = None) -> str
```

### VideoComposer
```python
class VideoComposer:
    def compose_final_video(original_video: str, dubbed_audio: str, 
                           lip_synced_video: str = None, output_path: str = None) -> str
    def add_subtitles(video_path: str, subtitle_file: str, output_path: str) -> str
    def create_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> str
```

### VideoSyncUtils
```python
class VideoSyncUtils:
    def extract_frames_at_timestamps(video_path: str, timestamps: List[float]) -> List[str]
    def detect_speech_segments(audio_path: str, min_duration: float = 0.5) -> List[Tuple[float, float]]
    def calculate_lip_sync_quality(original_video: str, synced_video: str) -> Dict[str, float]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

Same as the main Sonora project.

## 🆘 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This README and inline code comments

---

**Note**: This video dubbing system is an extension of the core Sonora audio dubbing pipeline. Make sure you have the base system working before using video features.








































