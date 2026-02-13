#!/usr/bin/env python3
"""
Test server startup and capture ALL errors.
"""

import sys
import traceback
import os
from pathlib import Path

print("=" * 60)
print("  TESTING SERVER STARTUP - ERROR CAPTURE")
print("=" * 60)
print()

# Set working directory
script_dir = Path(__file__).parent
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

print(f"Working directory: {os.getcwd()}")
print(f"Python: {sys.executable}")
print()

# Test 1: Import uvicorn
print("Test 1: Checking uvicorn...")
try:
    import uvicorn
    print(f"✅ uvicorn version: {uvicorn.__version__}")
except Exception as e:
    print(f"❌ uvicorn error: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

# Test 2: Import app
print("\nTest 2: Importing server app...")
try:
    from api.server import app
    print(f"✅ App imported: {type(app)}")
    print(f"   Routes: {len(app.routes)}")
except Exception as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

# Test 3: Try to start server
print("\nTest 3: Attempting to start server...")
print("=" * 60)
print("  STARTING SERVER ON http://127.0.0.1:8000")
print("=" * 60)
print()
print("If you see errors below, copy them:")
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
    print(f"\n❌ SERVER STARTUP ERROR:")
    print(f"   {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("COPY THE ERROR ABOVE AND SHARE IT")
    print("=" * 60)
    input("\nPress Enter to exit...")
    sys.exit(1)









