# Sonora Container Health Diagnostics
Write-Host ""
Write-Host "🔍 Running Sonora Container Diagnostics..." -ForegroundColor Cyan
Write-Host ""

$containerName = "sonora_all"

# Check if container exists and is running
Write-Host "📊 Container Status & Ports:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$containerStatus = docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" 2>&1
$containerStatus | Write-Host
if ($containerStatus -notmatch $containerName) {
    Write-Host "⚠️  Container '$containerName' not found or not running!" -ForegroundColor Red
    Write-Host "   Run: docker ps -a to see all containers" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check ports inside container
Write-Host "🔌 Checking Ports Inside Container:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$portCmd = 'ss -ltnp | egrep ":8000|:80|:8501|:9090|:3000" || true'
docker exec -it $containerName bash -lc $portCmd
Write-Host ""

# Supervisord logs
Write-Host "📋 Supervisord Logs (last 200 lines):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
docker exec -it $containerName tail -n 200 /var/log/supervisord.log
Write-Host ""

# FastAPI logs
Write-Host "📋 FastAPI Logs (last 200 lines):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
docker exec -it $containerName tail -n 200 /var/log/fastapi.log 2>&1
Write-Host ""

# Streamlit logs
Write-Host "📋 Streamlit Logs (last 200 lines):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
docker exec -it $containerName tail -n 200 /var/log/streamlit.log 2>&1
Write-Host ""

# Nginx error logs
Write-Host "📋 Nginx Error Logs (last 200 lines):" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
docker exec -it $containerName tail -n 200 /var/log/nginx/error.log 2>&1
Write-Host ""

# Health endpoints
Write-Host "🏥 Health Endpoints:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Write-Host "`n/health endpoint:" -ForegroundColor Cyan
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $healthResponse | ConvertTo-Json -Depth 10 | Write-Host
} catch {
    Write-Host "❌ Health endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n/health/live endpoint:" -ForegroundColor Cyan
try {
    $liveResponse = Invoke-RestMethod -Uri "http://localhost/health/live" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $liveResponse | ConvertTo-Json -Depth 10 | Write-Host
} catch {
    Write-Host "❌ Live endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n/metrics endpoint (first 40 lines):" -ForegroundColor Cyan
try {
    $metricsResponse = Invoke-WebRequest -Uri "http://localhost/metrics" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $metricsResponse.Content -split "`n" | Select-Object -First 40 | Write-Host
} catch {
    Write-Host "❌ Metrics endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Quick pipeline smoke test
Write-Host "🧪 Pipeline Smoke Test:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$testVideo = "tests/data/sample_multichar.mp4"
if (Test-Path $testVideo) {
    Write-Host "Testing with: $testVideo" -ForegroundColor Cyan
    Write-Host "Running curl command inside container..." -ForegroundColor Gray
    $curlCmd = "curl -X POST 'http://localhost/api/dub/video' -F 'file=@$testVideo' -F 'mode=multichar' -o /tmp/dub_response.json 2>&1"
    docker exec -it $containerName bash -lc $curlCmd
    Write-Host "Response:" -ForegroundColor Cyan
    $jsonCmd = 'cat /tmp/dub_response.json | python3 -m json.tool 2>/dev/null || cat /tmp/dub_response.json'
    docker exec -it $containerName bash -lc $jsonCmd
    Write-Host ""
    $jobIdCmd = "cat /tmp/dub_response.json | python3 -c `"import sys, json; print(json.load(sys.stdin).get('job_id', ''))`" 2>/dev/null"
    $jobId = docker exec -it $containerName bash -lc $jobIdCmd
    if ($jobId -and $jobId.Trim()) {
        Write-Host "Job ID: $jobId" -ForegroundColor Green
        Write-Host "Poll job status with: docker exec -it $containerName curl http://localhost/api/jobs/$jobId" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  Test video not found: $testVideo" -ForegroundColor Yellow
    Write-Host "   Skipping smoke test" -ForegroundColor Gray
    Write-Host "   Note: You can run this manually with:" -ForegroundColor Gray
    Write-Host "   docker exec -it $containerName curl -X POST 'http://localhost/api/dub/video' -F 'file=@tests/data/sample_multichar.mp4' -F 'mode=multichar'" -ForegroundColor Gray
}
Write-Host ""

# TTS duration check
Write-Host "🎵 TTS Duration Check:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
$ttsCheckScript = @'
import soundfile as sf, json, os
orig = 'tests/data/sample_segment_orig.wav'
gen = 'outputs/sample_segment_tts.wav'
if os.path.exists(orig) and os.path.exists(gen):
    o_d = sf.info(orig).duration
    g_d = sf.info(gen).duration
    print(f"orig: {o_d:.3f}s, gen: {g_d:.3f}s, diff: {g_d-o_d:.3f}s")
else:
    print("Files not found - skipping TTS check")
'@
docker exec -it $containerName python3 -c $ttsCheckScript 2>&1
Write-Host ""

# Diarization & embeddings quality check
Write-Host "Diarization and Embeddings Quality:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check if dub response exists inside container
Write-Host "Checking dub response for diarization data:" -ForegroundColor Cyan
$checkFile = docker exec -it $containerName bash -lc 'test -f /tmp/dub_response.json && echo "exists" || echo "not found"'
if ($checkFile -match "exists") {
    docker exec -it $containerName bash -lc 'cat /tmp/dub_response.json | python3 -m json.tool | grep -A 20 diarization || echo "No diarization data in response"'
} else {
    Write-Host "No dub response file found" -ForegroundColor Yellow
}

# Check profiles
Write-Host "`nProfiles directory:" -ForegroundColor Cyan
$profilesCmd = 'ls -la profiles/ 2>/dev/null || echo "profiles/ directory not found"'
docker exec -it $containerName bash -lc $profilesCmd

# Cluster similarity check
Write-Host "`nCluster similarity:" -ForegroundColor Cyan
$similarityScript = @'
import numpy as np, json, os
try:
    if os.path.exists('profiles'):
        profiles = [json.load(open(os.path.join('profiles', f))) for f in os.listdir('profiles') if f.endswith('.json')]
        if profiles:
            embs = [p['embedding'] for p in profiles if 'embedding' in p]
            if embs and len(embs) > 1:
                from sklearn.metrics.pairwise import cosine_similarity
                M = cosine_similarity(np.array(embs))
                triu_indices = np.triu_indices_from(M, k=1)
                triu_values = M[triu_indices]
                print("Profile similarity matrix: " + str(M.shape))
                print("Mean similarity: {:.4f}".format(triu_values.mean()))
                print("Min similarity: {:.4f}".format(triu_values.min()))
                print("Max similarity: {:.4f}".format(triu_values.max()))
            else:
                print("No embeddings found in profiles")
        else:
            print("No profile JSON files found")
    else:
        print("profiles/ directory not found")
except Exception as e:
    print("Error: " + str(e))
'@
docker exec -it $containerName python3 -c $similarityScript 2>&1
Write-Host ""

Write-Host "Diagnostics complete!" -ForegroundColor Green
Write-Host ""
