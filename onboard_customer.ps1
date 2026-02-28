# onboard_customer.ps1 - Sonora B2B Onboarding Utility (Windows)
# v1.1.0 (Production)

param (
    [Parameter(Mandatory = $true)]
    [string]$CustomerName
)

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "🎨 SONORA B2B: CUSTOMER ONBOARDING (WINDOWS)" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan

$CustomerId = $CustomerName.ToLower().Replace(" ", "")
$InstanceDir = "deployments\$CustomerId"
# Using a local data path for Windows simplicity, or the user can override
$DataDir = "$PSScriptRoot\data\$CustomerId"

Write-Host "➡️  Onboarding: $CustomerName (ID: $CustomerId)"

# 1. Hardware Pre-Flight Check
Write-Host "🔍 Checking hardware readiness..." -ForegroundColor Cyan
$HasGpu = $true

try {
    & nvidia-smi --query-gpu=name --format=csv, noheader | Out-Null
}
catch {
    Write-Host "⚠️  NVIDIA GPU not detected or drivers missing." -ForegroundColor Yellow
    $HasGpu = $false
}

if (-not $HasGpu) {
    $Choice = Read-Host "❌ WARNING: This instance will run in CPU-Legacy mode (Slow). Continue? (y/n)"
    if ($Choice -ne "y") {
        Write-Host "🚪 Aborting onboarding." -ForegroundColor Red
        exit
    }
}
else {
    Write-Host "✅ Hardware Ready: NVIDIA GPU detected." -ForegroundColor Green
}

# 2. Create Deployment and Data isolation
New-Item -ItemType Directory -Force -Path $InstanceDir | Out-Null
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# 2. Generate Secure API Key
$SonoraKey = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24)).ToLower()
Write-Host "✅ Generated secure API key: $SonoraKey" -ForegroundColor Green

# 3. Create .env from template
$EnvContent = @"
# SONORA PRODUCTION CONFIG - $CustomerName
SONORA_API_KEY=$SonoraKey
SONORA_CUSTOMER_ID=$CustomerId
SONORA_DATA_DIR=/app/sonora/data
LOG_LEVEL=INFO
"@

# Collect existing keys if any
if (Test-Path .env) {
    $ExistingEnv = Get-Content .env
    foreach ($line in $ExistingEnv) {
        if ($line -match "^(OPENAI_API_KEY|ELEVENLABS_API_KEY|ANTHROPIC_API_KEY)=") {
            $EnvContent += "`n$line"
        }
    }
}
else {
    Write-Host "⚠️  Global .env not found. Please add provider keys to $InstanceDir\.env manually later." -ForegroundColor Yellow
}

$EnvContent | Out-File -FilePath "$InstanceDir\.env" -Encoding utf8

# 4. Copy Docker Compose
Copy-Item "docker-compose.prod.yml" -Destination "$InstanceDir\"

# 5. Launch the Appliance
Write-Host "🚀 Launching instance for $CustomerName..." -ForegroundColor Magenta
Set-Location $InstanceDir
docker-compose -p "sonora-$CustomerId" up -d

# 6. Verify Service Health (Retry loop for cloud-side weight download)
$MaxRetries = 30 # 30 retries * 10s = 300s (5 minutes)
$RetryCount = 0
$Healthy = $false

Write-Host "📡 Verifying API connectivity (Waiting for neural handshake / model download)..." -ForegroundColor Cyan

while (-not $Healthy -and $RetryCount -lt $MaxRetries) {
    try {
        $Health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Headers @{"X-Sonora-Key" = $SonoraKey } -Method Get
        if ($Health.status -eq "ok") {
            $Healthy = $true
            Write-Host "✅ System Healthy: Orchestrator is online." -ForegroundColor Green
        }
    }
    catch {
        $RetryCount++
        if ($RetryCount % 6 -eq 0) { # Every minute
            Write-Host "⏳ Still waiting for system to warm up (Minute $($RetryCount / 6))..." -ForegroundColor Gray
        }
        Start-Sleep -Seconds 10
    }
}

if (-not $Healthy) {
    Write-Host "❌ Health check failed after 5 minutes. API may have failed to start or download is taking too long." -ForegroundColor Red
    Write-Host "   Check logs with: docker-compose -p sonora-$CustomerId logs sonora-api" -ForegroundColor Gray
}

Write-Host ""
Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "✨ ONBOARDING COMPLETE!" -ForegroundColor Green
Write-Host "Customer:    $CustomerName"
Write-Host "Service URL: http://localhost:8501"
Write-Host "API Key:     $SonoraKey"
Write-Host "Deploy Dir:  $InstanceDir"
Write-Host "Data Dir:    $DataDir"
Write-Host "------------------------------------------------" -ForegroundColor Cyan
