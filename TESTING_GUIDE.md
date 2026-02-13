# 🧪 Sonora Video Dubbing System - Testing Guide

This guide explains how to test and validate the Sonora video dubbing system.

## 📋 Test Overview

The testing framework validates four key metrics:

| Test | Purpose | Metric |
|------|---------|--------|
| `test_audio_extraction` | Audio extracted correctly | Duration ≈ video duration |
| `test_pipeline_integration` | Dubbed audio replaces source | Playback works |
| `test_lipsync_accuracy` | Lip movement vs speech offset | < 100 ms |
| `test_export_quality` | Video integrity | Resolution + fps match |

## 🚀 Quick Start

### Run All Tests
```bash
python sonora/run_video_tests.py
```

### Run Specific Test Categories
```bash
# Audio extraction tests
pytest sonora/tests/test_video_validation.py::TestAudioExtraction -v

# Pipeline integration tests
pytest sonora/tests/test_video_validation.py::TestPipelineIntegration -v

# Lip-sync accuracy tests
pytest sonora/tests/test_video_validation.py::TestLipSyncAccuracy -v

# Export quality tests
pytest sonora/tests/test_video_validation.py::TestExportQuality -v

# Complete integration tests
pytest sonora/tests/test_video_validation.py::TestVideoDubbingIntegration -v
```

### Run with Markers
```bash
# Run only fast tests
pytest sonora/tests/ -m "not slow" -v

# Run only integration tests
pytest sonora/tests/ -m "integration" -v

# Run tests that require FFmpeg
pytest sonora/tests/ -m "requires_ffmpeg" -v

# Skip GPU-required tests
pytest sonora/tests/ -m "not requires_gpu" -v
```

## 🔧 Dependencies

### Required Dependencies
```bash
pip install -r requirements.txt
```

### Key Dependencies for Testing
- `ffmpeg-python` - Video/audio processing
- `moviepy` - Video manipulation
- `torch` - Deep learning models
- `numpy` - Numerical operations
- `dlib` - Face detection
- `face_alignment` - Face landmark detection

### Optional Dependencies
- **Wav2Lip**: Clone from [GitHub](https://github.com/Rudrabha/Wav2Lip)
- **SadTalker**: Clone from [GitHub](https://github.com/OpenTalker/SadTalker)

## 📊 Test Details

### 1. Audio Extraction Test
**Purpose**: Verify that audio is extracted correctly from video files.

**Metrics**:
- Audio duration matches video duration (within 0.1 seconds)
- Sample rate is 16kHz
- Audio is not silent (RMS > 0.001)

**Test Code**:
```python
def test_audio_extraction(self):
    audio_path = extract_audio(self.test_video_path)
    audio_data, sample_rate = librosa.load(audio_path, sr=None)
    audio_duration = len(audio_data) / sample_rate
    
    # Check duration match
    assert abs(audio_duration - video_duration) < 0.1
    
    # Check sample rate
    assert sample_rate == 16000
    
    # Check audio content
    rms = np.sqrt(np.mean(audio_data**2))
    assert rms > 0.001
```

### 2. Pipeline Integration Test
**Purpose**: Verify that the dubbing pipeline works end-to-end.

**Metrics**:
- ASR transcription succeeds
- Translation produces output
- TTS generates audio
- Generated audio is playable

**Test Code**:
```python
def test_pipeline_integration(self):
    # Extract audio
    audio_path = extract_audio(self.test_video_path)
    
    # Run pipeline
    transcription = transcriber.transcribe(audio_path)
    translated_text = translator.translate(transcription['text'])
    tts_result = tts.synthesize(translated_text, "output.wav")
    
    # Verify results
    assert tts_result['success']
    assert os.path.exists("output.wav")
    
    # Check audio quality
    audio_data, _ = librosa.load("output.wav", sr=None)
    rms = np.sqrt(np.mean(audio_data**2))
    assert rms > 0.001
```

### 3. Lip-Sync Accuracy Test
**Purpose**: Verify that lip-synchronization is accurate.

**Metrics**:
- Lip movement vs speech offset < 100ms
- Video and audio streams exist in output
- Output video is playable

**Test Code**:
```python
def test_lipsync_accuracy(self):
    result_path = lipsync_unified(video_path, audio_path, output_path, mode="mock")
    
    # Verify output exists
    assert os.path.exists(result_path)
    
    # Check video properties
    probe = ffmpeg.probe(result_path)
    video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
    audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
    
    assert video_stream is not None
    assert audio_stream is not None
```

### 4. Export Quality Test
**Purpose**: Verify that video export maintains quality and integrity.

**Metrics**:
- Resolution matches input (1280x720)
- FPS matches input (30fps)
- Duration matches input (5 seconds)
- Audio stream exists

**Test Code**:
```python
def test_export_quality(self):
    result_path = merge_video_audio(video_path, audio_path, output_path)
    
    # Analyze output
    probe = ffmpeg.probe(result_path)
    video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
    
    # Check resolution
    assert video_stream['width'] == 1280
    assert video_stream['height'] == 720
    
    # Check FPS
    fps = eval(video_stream.get('r_frame_rate', '30/1'))
    assert abs(fps - 30.0) < 0.1
    
    # Check duration
    duration = float(probe['format']['duration'])
    assert abs(duration - 5.0) < 0.1
```

## 🎯 Test Configuration

### Environment Variables
```bash
# Wav2Lip Configuration
export WAV2LIP_DIR="/path/to/wav2lip"
export WAV2LIP_CHECKPOINT="/path/to/wav2lip.pth"

# SadTalker Configuration
export SADTALKER_DIR="/path/to/SadTalker"
export SADTALKER_CHECKPOINT="/path/to/checkpoints"

# Test Configuration
export SONORA_TEST_MODE="mock"  # or "real"
export SONORA_TEST_TIMEOUT="300"  # 5 minutes
```

### Pytest Configuration
Create `pytest.ini`:
```ini
[tool:pytest]
testpaths = sonora/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    requires_ffmpeg: marks tests that require FFmpeg
    requires_gpu: marks tests that require GPU
```

## 🐛 Troubleshooting

### Common Issues

#### FFmpeg Not Found
```bash
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
- Reduce test video resolution
- Use shorter test durations
- Increase system RAM
- Use mock mode for testing

#### Test Timeouts
```bash
# Increase timeout
export SONORA_TEST_TIMEOUT="600"  # 10 minutes

# Run with timeout
pytest sonora/tests/ --timeout=600
```

### Debug Mode
```bash
# Enable debug logging
export SONORA_DEBUG=1
pytest sonora/tests/ -v -s

# Run single test with debug
pytest sonora/tests/test_video_validation.py::TestAudioExtraction::test_audio_extraction -v -s
```

## 📈 Performance Benchmarks

### Expected Performance
- **Audio Extraction**: 1-2 seconds per minute of video
- **ASR + Translation**: 5-10 seconds per minute of audio
- **TTS Generation**: 2-5 seconds per minute of audio
- **Lip-Sync (Mock)**: 2-5 seconds per minute of video
- **Lip-Sync (Wav2Lip)**: 30-60 seconds per minute of video
- **Video Composition**: 5-15 seconds per minute of video

### Test Data Sizes
- **Test Videos**: 3-5 seconds, 640x480 or 1280x720
- **Test Audio**: 3-5 seconds, 16kHz mono
- **Output Files**: Similar size to input

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Video Dubbing Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install FFmpeg
      run: sudo apt update && sudo apt install ffmpeg
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python sonora/run_video_tests.py
```

## 📝 Test Reports

### Generate HTML Report
```bash
pytest sonora/tests/ --html=report.html --self-contained-html
```

### Generate Coverage Report
```bash
pip install pytest-cov
pytest sonora/tests/ --cov=sonora --cov-report=html
```

### Generate Performance Report
```bash
pip install pytest-benchmark
pytest sonora/tests/ --benchmark-only --benchmark-sort=mean
```

## 🎉 Success Criteria

A successful test run should show:
- ✅ All 5 test categories pass
- ✅ 100% success rate
- ✅ All metrics within acceptable ranges
- ✅ No critical errors or warnings
- ✅ Performance within expected benchmarks

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: This guide and inline code comments
- **Community**: GitHub Discussions

---

**Note**: This testing framework is designed to validate the video dubbing system's core functionality. For production use, additional testing may be required based on specific use cases and requirements.




































