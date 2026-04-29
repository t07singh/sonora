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
    
    # Check if we're in the right directory
    is_code_found = Path("api/server.py").exists() or Path("/app/api/server.py").exists() or Path(os.getenv("HOME", "")) .joinpath("app/api/server.py").exists()
    
    if not is_code_found:
        print("Error: api/server.py not found")
        print(f"Current Directory: {os.getcwd()}")
        print("Please run this script from the sonora project root directory.")
        return
    
    # Load environment variables from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    print("API Key Status:")
    if openai_key:
        print("✓ OPENAI_API_KEY found")
    else:
        print("⚠ OPENAI_API_KEY not found (using mock)")
        
    if gemini_key:
        print(f"✓ GEMINI_API_KEY found (starts with: {gemini_key[:4]}...)")
    else:
        print("⚠ GEMINI_API_KEY not found (TRANSCRIPTIONS WILL BE MOCKED)")

    if elevenlabs_key:
        print("✓ ELEVENLABS_API_KEY found")
    else:
        print("⚠ ELEVENLABS_API_KEY not found (using mock)")
    
    print("\nServer will be available at:")
    print("   http://0.0.0.0:8000")
    print("   http://0.0.0.0:8000/docs (API documentation)")
    print("   http://0.0.0.0:8000/health (health check)")
    print("\nStarting server...")
    
    # Import and run the server
    try:
        import uvicorn
        
        # Add current directory to path for imports
        sys.path.insert(0, os.getcwd())
        
        uvicorn.run(
            "api.server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            workers=1, # Single worker for stability in cloud
            timeout_keep_alive=1200
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
