# 🔍 Debug Server Startup Issues

## Current Status

✅ **Import works**: Server app can be imported successfully
❌ **Server not starting**: Background processes aren't working reliably

## 🔧 Solution: Start Server Manually

### Step 1: Open Command Prompt (NOT PowerShell)

1. Press `Win + R`
2. Type `cmd` and press Enter
3. Navigate to: `cd C:\Users\HP\.cursor\sonora`

### Step 2: Run the Debug Script

```cmd
START_SERVER_DEBUG.bat
```

**OR run directly:**
```cmd
py -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload
```

### Step 3: Watch for Errors

The window will show:
- ✅ **If successful**: "Uvicorn running on http://127.0.0.1:8000"
- ❌ **If error**: Full error message and traceback

## 🐛 Common Issues & Fixes

### Issue 1: "No module named 'sonora'"
**Fix**: Make sure you're in the `sonora` directory:
```cmd
cd C:\Users\HP\.cursor\sonora
```

### Issue 2: "attempted relative import beyond top-level package"
**Status**: ✅ FIXED - Import paths updated

### Issue 3: Port 8000 in use
**Check:**
```cmd
netstat -ano | findstr :8000
```

**Kill process:**
```cmd
taskkill /PID <PID_NUMBER> /F
```

### Issue 4: Import errors
**Install dependencies:**
```cmd
pip install -r requirements.txt
```

## ✅ What Success Looks Like

When the server starts successfully, you'll see:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
🔑 Model Status:
✅ Using offline translation models (Hugging Face Transformers)
✅ Using offline TTS models (Coqui TTS / VibeVoice)
ℹ️  All operations are now fully offline - no API keys required
🔧 Initializing dubbing components...
✅ Components initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 🎯 Verify It's Running

**Open in browser:**
```
http://127.0.0.1:8000/health
```

**Expected:**
```json
{
  "status": "ok",
  "uptime": 0.5,
  "translation": "local",
  "tts": "coqui/vibevoice",
  "components": {
    "transcriber": true,
    "translator": true,
    "tts_provider": true,
    "cache_manager": true
  }
}
```

## 📋 Quick Test Commands

**Test if server is running:**
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health
```

**Check what's on port 8000:**
```cmd
netstat -ano | findstr :8000
```

**Test import:**
```cmd
py -c "from api.server import app; print('OK')"
```

---

**🎯 Run `START_SERVER_DEBUG.bat` in Command Prompt and paste any errors you see!**









