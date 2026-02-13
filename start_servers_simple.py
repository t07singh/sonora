#!/usr/bin/env python3
"""Simple server starter that shows all errors."""

import sys
import subprocess
import time
from pathlib import Path

def start_api():
    """Start API server."""
    print("=" * 60)
    print("STARTING API SERVER")
    print("=" * 60)
    print()
    
    try:
        import uvicorn
        from api.server import app
        
        print("✅ Imports successful")
        print("Starting server on http://127.0.0.1:8000")
        print("Press Ctrl+C to stop")
        print()
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

def start_ui():
    """Start UI server."""
    print("=" * 60)
    print("STARTING UI SERVER")
    print("=" * 60)
    print()
    
    try:
        import streamlit.web.cli as stcli
        import sys
        
        print("✅ Streamlit imported")
        print("Starting UI on http://127.0.0.1:8501")
        print("Press Ctrl+C to stop")
        print()
        
        sys.argv = ["streamlit", "run", "ui/demo_app.py", 
                   "--server.port", "8501", 
                   "--server.address", "127.0.0.1"]
        stcli.main()
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            start_api()
        elif sys.argv[1] == "ui":
            start_ui()
        else:
            print("Usage: python start_servers_simple.py [api|ui]")
    else:
        print("Usage: python start_servers_simple.py [api|ui]")
        print()
        print("To start both, run in separate terminals:")
        print("  Terminal 1: python start_servers_simple.py api")
        print("  Terminal 2: python start_servers_simple.py ui")








