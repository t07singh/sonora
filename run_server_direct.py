#!/usr/bin/env python3
"""
Direct server runner - starts the server without uvicorn command line.
This ensures the server actually starts and stays running.
"""

import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

print("=" * 60)
print("  SONORA API SERVER - DIRECT START")
print("=" * 60)
print()
print(f"Working directory: {os.getcwd()}")
print(f"Python: {sys.executable}")
print()

# Test import first
print("Testing imports...")
try:
    from api.server import app
    print("✅ Server app imported successfully")
    print(f"   Routes: {len(app.routes)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

print()
print("=" * 60)
print("  STARTING SERVER")
print("=" * 60)
print()
print("Server URL: http://127.0.0.1:8000")
print("Health:     http://127.0.0.1:8000/health")
print("API Docs:   http://127.0.0.1:8000/docs")
print()
print("=" * 60)
print("  SERVER RUNNING - Keep this window open!")
print("=" * 60)
print()
print("Press Ctrl+C to stop the server")
print()

# Start server directly
try:
    import uvicorn
    
    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable reload for stability
        log_level="info",
        access_log=True
    )
except KeyboardInterrupt:
    print("\n\n✅ Server stopped by user")
except Exception as e:
    print(f"\n❌ Server error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)









