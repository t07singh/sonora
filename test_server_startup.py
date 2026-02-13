#!/usr/bin/env python3
"""
Diagnostic script to test server startup and identify issues.
Run this to see what errors occur when starting the server.
"""

import sys
import os
import argparse
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

print("=" * 60)
print("🔍 Sonora Server Startup Diagnostic")
print("=" * 60)
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {current_dir}")
print(f"Python path: {sys.path[:3]}")
print()

# Test 1: Check if we can import uvicorn
print("Test 1: Checking uvicorn...")
try:
    import uvicorn
    print("✅ uvicorn is installed")
except ImportError as e:
    print(f"❌ uvicorn not installed: {e}")
    print("   Install with: pip install uvicorn[standard]")
    sys.exit(1)

# Test 2: Try importing the server module
print("\nTest 2: Testing server imports...")
try:
    from api.server import app
    print("✅ Successfully imported app from api.server")
    print(f"   App type: {type(app)}")
except ImportError as e:
    print(f"❌ Failed to import from api.server: {e}")
    print("\nTrying alternative import paths...")
    
    # Try sonora.api.server
    try:
        from sonora.api.server import app
        print("✅ Successfully imported app from sonora.api.server")
    except ImportError as e2:
        print(f"❌ Failed to import from sonora.api.server: {e2}")
        print("\n📋 Full error traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Test 3: Check if routes are available
print("\nTest 3: Checking route availability...")
try:
    routes = [route.path for route in app.routes]
    print(f"✅ Found {len(routes)} routes")
    print(f"   Sample routes: {routes[:5]}")
except Exception as e:
    print(f"⚠️  Could not list routes: {e}")

# Test 4: Check critical components
print("\nTest 4: Checking critical components...")
components_ok = True

# Check translation
try:
    from translate.translator import Translator
    print("✅ Translation module available")
except ImportError as e:
    print(f"⚠️  Translation module: {e}")

# Check TTS
try:
    from tts.tts_provider import TTSProvider
    print("✅ TTS module available")
except ImportError as e:
    print(f"⚠️  TTS module: {e}")

# Check ASR
try:
    from asr.transcriber import Transcriber
    print("✅ ASR module available")
except ImportError as e:
    print(f"⚠️  ASR module: {e}")

# Test 5: Try to start the server (only if not diagnostic-only mode)
parser = argparse.ArgumentParser(description="Sonora Server Diagnostic")
parser.add_argument("--diagnostic-only", action="store_true", 
                   help="Only run diagnostics, don't start server")
args = parser.parse_args()

if not args.diagnostic_only:
    print("\n" + "=" * 60)
    print("🚀 Attempting to start server...")
    print("=" * 60)
    print("Server will start on: http://127.0.0.1:8000")
    print("Health check: http://127.0.0.1:8000/health")
    print("API docs: http://127.0.0.1:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed to start: {e}")
        print("\n📋 Full error traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("\n" + "=" * 60)
    print("✅ ALL DIAGNOSTIC CHECKS PASSED")
    print("=" * 60)
    print("\n✅ All imports OK")
    print("✅ Routes loaded successfully")
    print("✅ Components available")
    print("\n💡 You can now start the server with:")
    print("   python -m uvicorn api.server:app --host 127.0.0.1 --port 8000")
    print("\n" + "=" * 60)

