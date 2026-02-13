$SourcePath = "C:\Users\HP\.cursor\sonora-"
$DestPath = "c:\Users\HP\.gemini\antigravity\scratch\sonora_repo"

Write-Host "Starting migration..."
Write-Host "Source: $SourcePath"
Write-Host "Destination: $DestPath"

# 1. Verify Source
if (-not (Test-Path $SourcePath)) {
    Write-Error "Source path does not exist: $SourcePath"
    exit 1
}

# 2. Clean Destination (Preserve .git)
Write-Host "Cleaning destination (preserving .git)..."
Get-ChildItem -Path $DestPath -Exclude ".git", "migrate.ps1", ".gitignore" | Remove-Item -Recurse -Force

# 3. Copy Files
Write-Host "Copying files..."
Copy-Item -Path "$SourcePath\*" -Destination $DestPath -Recurse -Force

Write-Host "Migration complete."
