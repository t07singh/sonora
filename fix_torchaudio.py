"""
Patch torchaudio to add missing list_audio_backends method for SpeechBrain compatibility
"""
import torchaudio

# Add missing method if it doesn't exist
if not hasattr(torchaudio, 'list_audio_backends'):
    def list_audio_backends():
        """Return available audio backends (mock implementation for compatibility)"""
        # Return common backends that torchaudio typically supports
        return ['soundfile', 'sox']
    
    torchaudio.list_audio_backends = list_audio_backends
    print("✅ Patched torchaudio.list_audio_backends()")








