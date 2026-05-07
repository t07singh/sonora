# =============================================================================
# SONORA STUDIO — Colab UI Launcher
# =============================================================================
# This script starts the Sonora FastAPI Backend and React Frontend on Colab.
# It uses localtunnel to provide a public URL.
# =============================================================================

import subprocess, time, os, sys
from pathlib import Path

def run_command(cmd, log_file=None):
    if log_file:
        with open(log_file, "w") as f:
            return subprocess.Popen(cmd, stdout=f, stderr=f, shell=True)
    return subprocess.Popen(cmd, shell=True)

print("=" * 60)
print("🚀 SONORA STUDIO UI LAUNCHER (COLAB)")
print("=" * 60)

# 1. Install localtunnel
print("📦 Installing localtunnel...")
subprocess.run("npm install -g localtunnel", shell=True, capture_output=True)

# 2. Start Backend
print("🧠 Starting FastAPI Backend (Port 8000)...")
backend_proc = run_command("uvicorn api.server:app --host 0.0.0.0 --port 8000")

# 3. Start Frontend
print("🎨 Starting React Frontend (Port 3000)...")
# Check if node_modules exists
if not os.path.exists("node_modules"):
    print("   (First run: Installing npm packages...)")
    subprocess.run("npm install", shell=True, capture_output=True)

# Start React without opening browser
frontend_proc = run_command("PORT=3000 BROWSER=none npm start")

print("\n⏳ Waiting for services to warm up (15s)...")
time.sleep(15)

# 4. Get Public IP for localtunnel password
import requests
public_ip = requests.get('https://ipv4.icanhazip.com').text.strip()

print("\n" + "=" * 60)
print("🔗 SONORA STUDIO PUBLIC LINKS")
print("=" * 60)
print(f"💡 LOCALTUNNEL PASSWORD (IP): {public_ip}")
print("   (Enter this IP if localtunnel asks for a password)")
print("=" * 60)

print("\n--- BACKEND API URL ---")
print("Opening tunnel for port 8000...")
subprocess.Popen("lt --port 8000", shell=True)

print("\n--- FRONTEND UI URL ---")
print("Opening tunnel for port 3000...")
# This one will be synchronous so it keeps the cell running and shows the URL
try:
    subprocess.run("lt --port 3000", shell=True)
except KeyboardInterrupt:
    print("\n👋 Stopping Sonora Studio...")
    backend_proc.terminate()
    frontend_proc.terminate()
