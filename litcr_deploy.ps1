$ErrorActionPreference = "Stop"

# Configuration
$LIGHTNING_API_KEY = "b5efb1b0-95be-43f4-b10e-5263141672c0"
$USERNAME = "roshnis0238"
$REGISTRY = "litcr.io"
$PROJECT_PATH = "lit-container/roshnis0238/sonora-external-testing-project"
$IMAGE_NAME = "sonora"
$LOCAL_IMAGE = "sonora-unified:latest"

Write-Host "Starting Sonora Deployment to Lightning Container Registry (LitCR)..." -ForegroundColor Cyan

# Step 1: Login
Write-Host "Logging in to LitCR..." -ForegroundColor Yellow
$LIGHTNING_API_KEY | docker login $REGISTRY --username=$USERNAME --password-stdin
if ($LASTEXITCODE -ne 0) { throw "Login failed" }

# Step 2: Build
Write-Host "Building Sonora Unified image (Lean Build)..." -ForegroundColor Yellow
docker build -f Dockerfile.unified -t $LOCAL_IMAGE .
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

# Step 3: Tag
Write-Host "Tagging image..." -ForegroundColor Yellow
$REMOTE_IMAGE = "$REGISTRY/$PROJECT_PATH/$IMAGE_NAME"
docker tag $LOCAL_IMAGE $REMOTE_IMAGE
if ($LASTEXITCODE -ne 0) { throw "Tagging failed" }

# Step 4: Push
Write-Host "Pushing image to LitCR..." -ForegroundColor Yellow
docker push $REMOTE_IMAGE
if ($LASTEXITCODE -ne 0) { throw "Push failed. This is often a network timeout for large layers. Please run the script again." }

Write-Host "Deployment complete! Image pushed to: $REMOTE_IMAGE" -ForegroundColor Green
