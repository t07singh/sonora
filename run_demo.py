#!/usr/bin/env python3
"""
Startup script for the Sonora Streamlit demo app.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the Streamlit demo app."""
    print("🎬 Starting Sonora AI Dubbing Demo")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("ui/demo_app.py").exists():
        print("❌ Error: ui/demo_app.py not found")
        print("Please run this script from the sonora project root directory")
        return
    
    # Check if Streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found")
        print("Please install Streamlit:")
        print("   pip install streamlit")
        return
    
    # Check if API server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("⚠️  API server may not be running properly")
    except:
        print("⚠️  API server is not running")
        print("Please start the API server first:")
        print("   python run_server.py")
        print("")
        print("The demo will still work in mock mode")
    
    print("\n🌐 Demo will be available at:")
    print("   http://localhost:8501")
    print("\n🔄 Starting Streamlit demo...")
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/demo_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Failed to start demo: {e}")

if __name__ == "__main__":
    main()


