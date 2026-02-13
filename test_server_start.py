#!/usr/bin/env python3
"""Quick test to start the server and see errors."""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("TESTING SERVER STARTUP")
print("=" * 60)
print()

# Test imports
print("Testing imports...")
try:
    from api.server import app
    print("✅ App imported successfully")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("Starting server on http://127.0.0.1:8000")
print("Press Ctrl+C to stop")
print()

try:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"\n❌ Server error: {e}")
    import traceback
    traceback.print_exc()
