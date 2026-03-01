#!/usr/bin/env python3
"""
Startup script for the Sonora API server.
"""

import os
import sys
from pathlib import Path

# Add current directory and sonora package to path for imports
current_dir = str(Path(__file__).parent)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

def main():
    """Start the API server."""
    print("Starting Sonora/Auralis AI Dubbing API Server")
    print("=" * 50)
    
    # Check if we're in the right directory or in Docker (/app)
    is_docker = Path("/app/api/server.py").exists()
    is_local = Path("api/server.py").exists()
    
    if not (is_docker or is_local):
        print("Error: api/server.py not found")
        print("Please run this script from the sonora project root directory or ensure volume is mapped.")
        return
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    
    print("API Key Status:")
    if openai_key:
        print("OPENAI_API_KEY found")
    else:
        print("OPENAI_API_KEY not found (will use mock mode)")
    
    if elevenlabs_key:
        print("ELEVENLABS_API_KEY found")
    else:
        print("ELEVENLABS_API_KEY not found (will use mock mode)")
    
    print("\nServer will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs (API documentation)")
    print("   http://localhost:8000/health (health check)")
    print("\nAPI Endpoints:")
    print("   POST /api/dub - Upload audio file for dubbing")
    print("\nStarting server...")
    
    # Import and run the server
    try:
        import uvicorn
        
        # Add current directory to path for imports
        current_dir = str(Path(__file__).resolve().parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # In Docker, we are mapped to /app
        if "/app" not in sys.path:
            sys.path.insert(0, "/app")
        
        # Try to import the app - first try direct import, then package import
        try:
            from api.server import app
            print("✓ Using direct import (api.server)")
        except ImportError:
            try:
                from sonora.api.server import app
                print("✓ Using package import (sonora.api.server)")
            except ImportError:
                # Last resort: try uvicorn with module string
                print("⚠ Using uvicorn module string import")
                uvicorn.run(
                    "api.server:app",
                    host="0.0.0.0",
                    port=8000,
                    reload=False,
                    log_level="info"
                )
                return
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid import issues
            log_level="info"
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required dependencies:")
        print("   pip install fastapi uvicorn python-multipart")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
