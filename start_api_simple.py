#!/usr/bin/env python3
"""
Simple startup script for Sonora API server with proper path setup.
"""
import os
import sys
from pathlib import Path

# Get the sonora directory
sonora_dir = Path(__file__).parent
parent_dir = sonora_dir.parent

# Add both directories to Python path
if str(sonora_dir) not in sys.path:
    sys.path.insert(0, str(sonora_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Change to sonora directory
os.chdir(sonora_dir)

print("Starting Sonora API Server...")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

try:
    import uvicorn
    
    # Try to import the app with fallback
    try:
        from api.server import app
        print("✓ Imported app from api.server")
    except ImportError as e1:
        print(f"First import failed: {e1}")
        try:
            # Try with sonora prefix
            from sonora.api.server import app
            print("✓ Imported app from sonora.api.server")
        except ImportError as e2:
            print(f"Second import failed: {e2}")
            # Try using uvicorn's module string
            print("⚠ Trying uvicorn module string...")
            uvicorn.run(
                "api.server:app",
                host="127.0.0.1",
                port=8000,
                reload=False,
                log_level="info"
            )
            sys.exit(0)
    
    print("\nServer starting on http://127.0.0.1:8000")
    print("API docs: http://127.0.0.1:8000/docs")
    print("Health: http://127.0.0.1:8000/health\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
    
except Exception as e:
    print(f"\n❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")










