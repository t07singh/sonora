# Sonora/Auralis - Anime-First AI Dubbing System

A modular AI dubbing pipeline designed specifically for anime content, featuring high-quality speech synthesis, intelligent translation, and non-verbal preservation.

## 🎯 Overview

Sonora/Auralis is a comprehensive AI dubbing system that transforms Japanese anime audio into high-quality English dubs while preserving the original's emotional impact, sound effects, and background music.

## 🏗️ Architecture

The system follows a modular design with independent components:

```
sonora/
├── asr/                    # Automatic Speech Recognition
│   ├── __init__.py
│   └── whisper_asr.py     # Whisper-based transcription
├── translate/              # Translation Services
│   ├── __init__.py
│   └── llm_translator.py  # LLM-based translation
├── tts/                    # Text-to-Speech
│   ├── __init__.py
│   ├── base_tts.py        # Base TTS interface
│   └── elevenlabs_tts.py  # ElevenLabs implementation
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── audio_utils.py     # Audio processing
│   └── sync_utils.py      # Synchronization
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py        # Settings management
├── api/                    # API Layer (FastAPI)
├── tests/                  # Test Suite
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🔄 Pipeline Flow

1. **ASR (Whisper)** → Transcribes Japanese/English with word-level timestamps
2. **Translation (LLM)** → Translates Japanese to English, preserves English unchanged
3. **TTS (Modular)** → ElevenLabs for MVP, VibeVoice for future
4. **Non-verbal Preservation** → Extracts SFX, laughs, shouts, BGM
5. **Sync & Timing** → Aligns dubbed voice with original timing
6. **Audio Muxer** → Combines new voices with preserved elements
7. **API Layer** → FastAPI backend with optional Streamlit UI

## 🚀 Features

### Core Capabilities
- **Multi-language ASR**: Japanese and English transcription with Whisper
- **Intelligent Translation**: LLM-powered translation with anime context awareness
- **High-quality TTS**: ElevenLabs integration with anime-optimized voice settings
- **Non-verbal Preservation**: Automatic detection and preservation of SFX, laughs, BGM
- **Audio Synchronization**: Precise timing alignment and lip-sync support
- **Modular Design**: Easy provider switching and feature extension

### Technical Features
- **Config-driven**: Swap TTS providers with configuration changes
- **Async Support**: Full async/await support for high performance
- **Error Handling**: Comprehensive error handling and logging
- **Type Safety**: Full type hints and Pydantic validation
- **Testing Ready**: Structured for unit and integration testing
- **Cache Monitoring**: Real-time cache performance monitoring and management
- **REST API**: FastAPI endpoints for cache statistics and control

## 📦 Installation

### Prerequisites
- Python 3.8+
- Git (for version control)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd sonora

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the project root:

```env
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# OpenAI Configuration (for translation)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration (alternative translation)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Audio Settings
AUDIO__SAMPLE_RATE=44100
AUDIO__CHANNELS=2
AUDIO__BIT_DEPTH=16

# API Settings
API__HOST=0.0.0.0
API__PORT=8000
API__DEBUG=false
```

## 🎮 Usage

### Quick Start with Cache Monitoring

1. **Start the API Server**:
```bash
python -m sonora.api.server
```

2. **Launch the Demo App** (with cache monitoring):
```bash
streamlit run sonora/ui/demo_app.py
```

3. **Access Cache Dashboard** (dedicated monitoring):
```bash
python -m sonora.run_cache_dashboard
```

The demo app now includes real-time cache monitoring in the sidebar, showing:
- Memory and disk cache usage
- Hit rate performance
- Cache size and uptime
- Manual cache clearing controls

### Basic Usage

```python
from sonora.asr import WhisperASR
from sonora.translate import LLMTranslator
from sonora.tts import ElevenLabsTTS
from sonora.utils import AudioProcessor, NonVerbalPreserver

# Initialize components
asr = WhisperASR()
translator = LLMTranslator()
tts = ElevenLabsTTS()
audio_processor = AudioProcessor()
preserver = NonVerbalPreserver()

# Process audio file
async def dub_audio(audio_path: str):
    # 1. Transcribe audio
    transcription = asr.transcribe(audio_path)
    
    # 2. Translate if needed
    if transcription.language == "ja":
        translation = await translator.translate(transcription.text)
        text_to_synthesize = translation.translated_text
    else:
        text_to_synthesize = transcription.text
    
    # 3. Preserve non-verbal elements
    non_verbal = preserver.detect_non_verbal_elements(
        audio_data, transcription.segments
    )
    
    # 4. Synthesize new voice
    tts_result = await tts.synthesize(text_to_synthesize)
    
    # 5. Mix and synchronize
    final_audio = audio_processor.mix_audio([
        tts_result.audio_data,
        non_verbal["bgm"],
        non_verbal["sfx"]
    ])
    
    return final_audio
```

### Configuration

```python
from sonora.config import settings

# Switch TTS provider
settings.tts.provider = "elevenlabs"  # or "vibevoice" in future

# Adjust voice settings for anime
tts.set_voice_settings(
    stability=0.75,
    similarity_boost=0.8,
    style=0.2,
    use_speaker_boost=True
)

# Configure translation
settings.translation.provider = "openai"  # or "anthropic"
settings.translation.model_name = "gpt-4"
```

## 🔧 Configuration

The system uses Pydantic Settings for configuration management:

### ASR Configuration
- `model_name`: Whisper model to use
- `language`: Language code (auto-detect if None)
- `temperature`: Transcription temperature
- `word_timestamps`: Enable word-level timestamps

### Translation Configuration
- `provider`: Translation provider ("openai" or "anthropic")
- `model_name`: Model for translation
- `temperature`: Translation temperature
- `max_tokens`: Maximum tokens per request

### TTS Configuration
- `provider`: TTS provider ("elevenlabs" or "vibevoice")
- `elevenlabs_api_key`: ElevenLabs API key
- `elevenlabs_voice_id`: Voice ID to use
- `elevenlabs_model`: Model for synthesis

### Audio Configuration
- `sample_rate`: Audio sample rate
- `channels`: Audio channels
- `bit_depth`: Audio bit depth
- `preserve_sfx`: Preserve sound effects
- `preserve_laughs`: Preserve laughs and shouts
- `preserve_bgm`: Preserve background music

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=sonora tests/

# Run specific test module
pytest tests/test_asr.py
```

## 🚀 Future Roadmap

### Phase 1 (MVP) - Current
- ✅ Whisper ASR integration
- ✅ OpenAI/Anthropic translation
- ✅ ElevenLabs TTS
- ✅ Basic audio processing
- ✅ Configuration system
- ✅ Cache monitoring system
- ✅ REST API endpoints
- ✅ Streamlit demo app with cache monitoring

### Phase 2 (Enhanced)
- 🔄 VibeVoice TTS integration
- 🔄 Advanced lip-sync algorithms
- 🔄 Real-time processing
- 🔄 Web UI (Streamlit)
- 🔄 Batch processing

### Phase 3 (Production)
- 📋 Multi-language support
- 📋 Voice cloning capabilities
- 📋 Advanced audio effects
- 📋 Cloud deployment
- 📋 Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for Whisper ASR models
- ElevenLabs for high-quality TTS
- The anime community for inspiration and feedback

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Join our Discord community
- Check the documentation wiki

---

**Sonora/Auralis** - Bringing anime to life with AI-powered dubbing 🎌✨

