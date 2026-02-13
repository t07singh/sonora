#!/usr/bin/env python3
"""
🎌 Sonora Website Launcher
Quick launcher for the beautiful anime-themed Sonora website.
"""

import os
import sys
import webbrowser
import time
import subprocess
from pathlib import Path

def main():
    """Launch the Sonora website."""
    print("🎌 Sonora - AI Anime Dubbing Website")
    print("=" * 50)
    print("🚀 Launching the beautiful anime-themed website...")
    print()
    
    # Change to website directory
    website_dir = Path(__file__).parent / "website"
    
    if not website_dir.exists():
        print("❌ Website directory not found!")
        return
    
    os.chdir(website_dir)
    
    try:
        # Start the server
        print("🌐 Starting web server on http://localhost:3000")
        print("📱 The website will open in your browser automatically")
        print("🛑 Press Ctrl+C to stop the server")
        print()
        
        # Import and run the server
        from server import main as server_main
        
        # Start server in background and open browser
        import threading
        server_thread = threading.Thread(target=server_main, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Open browser
        try:
            webbrowser.open('http://localhost:3000')
            print("✅ Website opened in your browser!")
        except:
            print("🌐 Please open http://localhost:3000 in your browser")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Website server stopped. Goodbye!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you're in the correct directory and have Python installed")

if __name__ == '__main__':
    main()



























