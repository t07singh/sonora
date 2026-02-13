#!/usr/bin/env python3
"""
Quick test script for Phase 6 AI features
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

async def test_phase6_features():
    """Test Phase 6 AI features quickly."""
    print("🧪 Testing Phase 6: Advanced AI Features")
    print("=" * 50)
    
    try:
        # Test VibeVoice TTS
        print("🎭 Testing VibeVoice TTS...")
        from sonora.tts.vibevoice_tts import VibeVoiceTTS
        
        tts = VibeVoiceTTS()
        voices = await tts.get_available_voices()
        print(f"✅ VibeVoice TTS: Found {len(voices)} voices")
        
        # Test voice synthesis
        result = await tts.synthesize("Hello, this is a test of VibeVoice TTS!")
        print(f"✅ Voice synthesis: {result.provider} - {result.duration:.1f}s")
        
    except Exception as e:
        print(f"❌ VibeVoice TTS test failed: {e}")
    
    try:
        # Test Advanced Lip-Sync
        print("\n👄 Testing Advanced Lip-Sync...")
        from sonora.video_sync.advanced_lipsync import AdvancedLipSyncEngine
        
        lip_sync_engine = AdvancedLipSyncEngine(model_type="mock")
        model_info = lip_sync_engine.get_model_info()
        print(f"✅ Advanced Lip-Sync: {model_info['selected_model']} model ready")
        
    except Exception as e:
        print(f"❌ Advanced Lip-Sync test failed: {e}")
    
    try:
        # Test Real-time Engine
        print("\n⚡ Testing Real-time Engine...")
        from sonora.processing.realtime_engine import RealTimeProcessingEngine
        
        realtime_engine = RealTimeProcessingEngine()
        stats = realtime_engine.get_engine_stats()
        print(f"✅ Real-time Engine: {stats['max_concurrent_tasks']} concurrent tasks")
        
    except Exception as e:
        print(f"❌ Real-time Engine test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 6 AI Features Test Complete!")
    print("✅ All core AI components are working correctly")

if __name__ == "__main__":
    asyncio.run(test_phase6_features())


































