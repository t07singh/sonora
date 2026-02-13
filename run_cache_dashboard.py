#!/usr/bin/env python3
"""
Launch script for the Sonora Cache Monitoring Dashboard.

This script starts the Streamlit cache monitoring dashboard.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the cache monitoring dashboard."""
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Path to the dashboard
    dashboard_path = script_dir / "ui" / "cache_dashboard.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found at: {dashboard_path}")
        sys.exit(1)
    
    print("🧠 Starting Sonora Cache Monitoring Dashboard...")
    print("=" * 50)
    print("📊 Dashboard will be available at: http://localhost:8501")
    print("🔗 Make sure the FastAPI server is running on port 8000")
    print("=" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()










