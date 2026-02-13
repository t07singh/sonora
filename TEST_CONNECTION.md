# Test Sonora Connection

## Quick Test Commands

### 1. Test API Health
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing

# Or in browser
# http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "uptime": 123.45,
  "services": {
    "asr": true,
    "tts": true,
    "lipsync": true
  }
}
```

### 2. Test API Docs
Open in browser: http://localhost:8000/docs

Should show interactive API documentation.

### 3. Test Streamlit UI
Open in browser: http://localhost:8501

Should show the Sonora demo interface.

### 4. Test from Streamlit UI
1. Open http://localhost:8501
2. Click "🔍 Check API Health" in the sidebar
3. Should see: ✅ API is online!

## Troubleshooting

### API Not Responding
```powershell
# Check if port 8000 is in use
netstat -ano | findstr ":8000"

# Check if Python process is running
Get-Process python -ErrorAction SilentlyContinue
```

### Common Errors

#### "Connection refused"
- API server not started
- Wrong port (check if 8000 is in use)
- Firewall blocking

#### "Module not found"
```powershell
# Install dependencies
python -m pip install fastapi uvicorn streamlit
```

#### "Address already in use"
```powershell
# Find and kill process on port 8000
$process = Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force
```

