#!/bin/bash
# Sonora Diagnostic Checks Script (Bash version)
# Run this script to get a comprehensive health picture of the Sonora container

echo "🔍 Sonora Diagnostic Checks"
echo "==========================="
echo ""

# 1. Containers & Ports
echo "1️⃣  Checking container status and ports..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "Checking ports inside container..."
docker exec -it sonora_all bash -lc "ss -ltnp | egrep ':8000|:80|:8501|:9090|:3000' || true"
echo ""

# 2. Supervisord & Service Logs
echo "2️⃣  Checking Supervisord and service logs..."
echo "--- Supervisord Log (last 200 lines) ---"
docker exec -it sonora_all tail -n 200 /var/log/supervisord.log
echo ""

echo "--- FastAPI Log (last 200 lines) ---"
docker exec -it sonora_all tail -n 200 /var/log/fastapi.log
echo ""

echo "--- Streamlit Log (last 200 lines) ---"
docker exec -it sonora_all tail -n 200 /var/log/streamlit.log
echo ""

echo "--- Nginx Error Log (last 200 lines) ---"
docker exec -it sonora_all tail -n 200 /var/log/nginx/error.log
echo ""

# 3. Health Endpoints
echo "3️⃣  Checking health endpoints..."
echo "--- /health endpoint ---"
curl -sSf http://localhost/health | jq . || echo "❌ Failed"
echo ""

echo "--- /health/live endpoint ---"
curl -sSf http://localhost/health/live | jq . || echo "❌ Failed"
echo ""

echo "--- /metrics endpoint (first 40 lines) ---"
curl -sSf http://localhost/metrics | head -n 40 || echo "❌ Failed"
echo ""

# 4. Pipeline Smoke Test
echo "4️⃣  Running pipeline smoke test..."
if [ -f "tests/data/sample_multichar.mp4" ]; then
    curl -X POST "http://localhost/api/dub/video" \
        -F "file=@tests/data/sample_multichar.mp4" \
        -F "mode=multichar" \
        -o /tmp/dub_response.json
    
    if [ $? -eq 0 ]; then
        echo "✅ Pipeline test response:"
        jq . /tmp/dub_response.json
        echo ""
        
        JOB_ID=$(jq -r '.job_id // empty' /tmp/dub_response.json)
        if [ -n "$JOB_ID" ]; then
            echo "💡 Job ID: $JOB_ID - Poll /api/jobs/$JOB_ID for status"
            echo ""
        fi
    else
        echo "❌ Pipeline test failed"
        echo ""
    fi
else
    echo "⚠️  Test file not found: tests/data/sample_multichar.mp4"
    echo ""
fi

# 5. TTS Duration Match Check
echo "5️⃣  TTS Duration Match Check..."
docker exec -it sonora_all python3 - <<'PY'
import soundfile as sf
import json
import os

orig = 'tests/data/sample_segment_orig.wav'
gen = 'outputs/sample_segment_tts.wav'

try:
    if os.path.exists(orig) and os.path.exists(gen):
        o_d = sf.info(orig).duration
        g_d = sf.info(gen).duration
        diff = g_d - o_d
        print(f"✅ Original: {o_d:.3f}s, Generated: {g_d:.3f}s, Diff: {diff:.3f}s")
    else:
        print(f"⚠️  Files not found: orig={os.path.exists(orig)}, gen={os.path.exists(gen)}")
except Exception as e:
    print(f"❌ Error: {e}")
PY
echo ""

# 6. Diarization & Embeddings Quality
echo "6️⃣  Diarization & Embeddings Quality Check..."
if [ -f "/tmp/dub_response.json" ]; then
    echo "--- Diarization segments ---"
    jq '.diarization' /tmp/dub_response.json || echo "No diarization data"
    echo ""
fi

echo "--- Profile files ---"
docker exec -it sonora_all bash -lc "ls -la profiles/ 2>/dev/null || echo 'No profiles directory'"
echo ""

echo "--- Cluster similarity check ---"
docker exec -it sonora_all python3 - <<'PY'
import numpy as np
import json
import os
from pathlib import Path

profiles_dir = Path('profiles')
if profiles_dir.exists():
    profile_files = list(profiles_dir.glob('*.json'))
    if profile_files:
        profiles = []
        for f in profile_files:
            try:
                with open(f, 'r') as file:
                    profiles.append(json.load(file))
            except Exception as e:
                print(f"Error reading {f}: {e}")
        
        if profiles:
            embs = [p.get('embedding', []) for p in profiles if 'embedding' in p]
            if embs:
                try:
                    from sklearn.metrics.pairwise import cosine_similarity
                    M = cosine_similarity(np.array(embs))
                    print(f"✅ Profile similarity matrix: {M.shape}")
                    print(f"   Mean similarity: {M[np.triu_indices_from(M, k=1)].mean():.3f}")
                    print(f"   Min similarity: {M[np.triu_indices_from(M, k=1)].min():.3f}")
                    print(f"   Max similarity: {M[np.triu_indices_from(M, k=1)].max():.3f}")
                except ImportError:
                    print("⚠️  sklearn not available for similarity check")
                except Exception as e:
                    print(f"❌ Error calculating similarity: {e}")
            else:
                print("⚠️  No embeddings found in profiles")
        else:
            print("⚠️  No valid profiles loaded")
    else:
        print("⚠️  No profile JSON files found")
else:
    print("⚠️  Profiles directory not found")
PY
echo ""

echo "✅ Diagnostic checks complete!"

