# Sonora Diagnostic Checks Script
# Run this script to get a comprehensive health picture of the Sonora container

Write-Host "🔍 Sonora Diagnostic Checks" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is available
$dockerAvailable = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerAvailable) {
    Write-Host "⚠️  Docker not found in PATH. Please ensure Docker Desktop is running." -ForegroundColor Yellow
    Write-Host ""
}

# 1. Containers & Ports
Write-Host "1️⃣  Checking container status and ports..." -ForegroundColor Yellow
if ($dockerAvailable) {
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host ""
    
    Write-Host "Checking ports inside container..." -ForegroundColor Gray
    docker exec -it sonora_all bash -lc "ss -ltnp | egrep ':8000|:80|:8501|:9090|:3000' || true"
    Write-Host ""
} else {
    Write-Host "   ⏭️  Skipped (Docker not available)" -ForegroundColor Gray
    Write-Host ""
}

# 2. Supervisord & Service Logs
Write-Host "2️⃣  Checking Supervisord and service logs..." -ForegroundColor Yellow
if ($dockerAvailable) {
    Write-Host "--- Supervisord Log (last 200 lines) ---" -ForegroundColor Gray
    docker exec -it sonora_all tail -n 200 /var/log/supervisord.log
    Write-Host ""
    
    Write-Host "--- FastAPI Log (last 200 lines) ---" -ForegroundColor Gray
    docker exec -it sonora_all tail -n 200 /var/log/fastapi.log
    Write-Host ""
    
    Write-Host "--- Streamlit Log (last 200 lines) ---" -ForegroundColor Gray
    docker exec -it sonora_all tail -n 200 /var/log/streamlit.log
    Write-Host ""
    
    Write-Host "--- Nginx Error Log (last 200 lines) ---" -ForegroundColor Gray
    docker exec -it sonora_all tail -n 200 /var/log/nginx/error.log
    Write-Host ""
} else {
    Write-Host "   ⏭️  Skipped (Docker not available)" -ForegroundColor Gray
    Write-Host ""
}

# 3. Health Endpoints
Write-Host "3️⃣  Checking health endpoints..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ /health endpoint:" -ForegroundColor Green
    $healthResponse.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    Write-Host ""
} catch {
    Write-Host "❌ /health endpoint failed: $_" -ForegroundColor Red
    Write-Host ""
}

try {
    $liveResponse = Invoke-WebRequest -Uri "http://localhost/health/live" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ /health/live endpoint:" -ForegroundColor Green
    $liveResponse.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    Write-Host ""
} catch {
    Write-Host "❌ /health/live endpoint failed: $_" -ForegroundColor Red
    Write-Host ""
}

try {
    $metricsResponse = Invoke-WebRequest -Uri "http://localhost/metrics" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ /metrics endpoint (first 40 lines):" -ForegroundColor Green
    $metricsResponse.Content -split "`n" | Select-Object -First 40
    Write-Host ""
} catch {
    Write-Host "❌ /metrics endpoint failed: $_" -ForegroundColor Red
    Write-Host ""
}

# 4. Pipeline Smoke Test
Write-Host "4️⃣  Running pipeline smoke test..." -ForegroundColor Yellow
$testFile = "tests/data/sample_multichar.mp4"
if (Test-Path $testFile) {
    try {
        $multipartContent = [System.Net.Http.MultipartFormDataContent]::new()
        $fileStream = [System.IO.File]::OpenRead($testFile)
        $fileContent = [System.Net.Http.StreamContent]::new($fileStream)
        $fileContent.Headers.ContentDisposition = [System.Net.Http.Headers.ContentDispositionHeaderValue]::new("form-data")
        $fileContent.Headers.ContentDisposition.Name = "file"
        $fileContent.Headers.ContentDisposition.FileName = [System.IO.Path]::GetFileName($testFile)
        $multipartContent.Add($fileContent, "file")
        $multipartContent.Add([System.Net.Http.StringContent]::new("multichar"), "mode")
        
        $response = Invoke-WebRequest -Uri "http://localhost/api/dub/video" -Method POST -Body $multipartContent -ErrorAction Stop
        $responseJson = $response.Content | ConvertFrom-Json
        Write-Host "✅ Pipeline test response:" -ForegroundColor Green
        $responseJson | ConvertTo-Json -Depth 10
        Write-Host ""
        
        # If job_id exists, note it
        if ($responseJson.job_id) {
            Write-Host "💡 Job ID: $($responseJson.job_id) - Poll /api/jobs/$($responseJson.job_id) for status" -ForegroundColor Cyan
            Write-Host ""
        }
    } catch {
        Write-Host "❌ Pipeline test failed: $_" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "⚠️  Test file not found: $testFile" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "✅ Diagnostic checks complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: For TTS duration match and diarization checks, run the Python scripts inside the container:" -ForegroundColor Cyan
Write-Host "   docker exec -it sonora_all bash" -ForegroundColor Gray
Write-Host ""

