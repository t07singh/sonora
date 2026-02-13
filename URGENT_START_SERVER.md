# 🚨 URGENT: Start Server - Step by Step

## The Problem

The server is NOT running, which is why you see "connection refused".

## ✅ Solution: Start It Manually (REQUIRED)

**You MUST run the server in a terminal window yourself.** Background processes don't work reliably.

## 📋 Step-by-Step Instructions

### Step 1: Open Command Prompt
- Press `Win + R`
- Type `cmd` and press Enter
- **DO NOT use PowerShell** (use Command Prompt)

### Step 2: Navigate to Sonora
```cmd
cd C:\Users\HP\.cursor\sonora
```

### Step 3: Run ONE of These

**Option A (Recommended - checks everything first):**
```cmd
CHECK_AND_START.bat
```

**Option B (Simple - just starts server):**
```cmd
start_server_simple.bat
```

**Option C (Direct Python):**
```cmd
py run_server_direct.py
```

**Option D (Uvicorn command):**
```cmd
py -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload
```

## ✅ What Success Looks Like

You MUST see this in the terminal:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 🎯 Verify It's Running

**While the server window is open**, test in another terminal:
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health
```

**Or open in browser:**
```
http://127.0.0.1:8000/health
```

## ❌ If You See Errors

**Copy the ENTIRE error message** from the terminal and share it.

Common errors:
- "Port already in use" → The batch file will help kill it
- "Module not found" → Run `pip install -r requirements.txt`
- "Import error" → Already fixed, but let me know if you see one

## 💡 Critical Points

1. **The terminal window MUST stay open** - closing it stops the server
2. **You MUST see "Uvicorn running"** - if you don't, the server didn't start
3. **Test the health endpoint** - if it works, the server is running
4. **Keep the server running** - don't close the terminal until you're done

## 🔍 Debug Checklist

- [ ] Are you in the correct directory? (`C:\Users\HP\.cursor\sonora`)
- [ ] Is Python working? (`py --version`)
- [ ] Are imports working? (`py -c "from api.server import app"`)
- [ ] Is port 8000 free? (`netstat -ano | findstr :8000`)
- [ ] Did you see "Uvicorn running" message?

---

**🎯 Run `CHECK_AND_START.bat` in Command Prompt NOW and tell me what you see!**









