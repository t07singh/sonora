# ⚠️ CRITICAL: Check the PowerShell Windows NOW

## The Problem
Both API and UI servers are failing to start. The error messages are in the PowerShell windows that opened.

## 🔍 What You Need to Do RIGHT NOW

### Step 1: Find the PowerShell Windows

Look for these windows on your screen:
1. **"=== SONORA API SERVER ==="** - This shows API errors
2. **"=== SONORA UI ==="** - This shows UI errors

They may be:
- Minimized in the taskbar
- Behind other windows
- Showing errors in red text

### Step 2: Check the API Window

**Look for:**
- ✅ Success: `INFO: Uvicorn running on http://0.0.0.0:8000`
- ❌ Error: `ModuleNotFoundError: No module named 'app'`
- ❌ Error: `ImportError: cannot import name 'app'`
- ❌ Error: Any red error text

**Copy the EXACT error message** you see.

### Step 3: Check the UI Window

**Look for:**
- ✅ Success: `You can now view your Streamlit app`
- ❌ Error: `FileNotFoundError`
- ❌ Error: `ModuleNotFoundError`
- ❌ Error: Any red error text

**Copy the EXACT error message** you see.

## 🛠️ Common Errors & Quick Fixes

### Error: "No module named 'app'"
**This means wrong directory.**
**Fix:**
```powershell
cd C:\Users\HP\.cursor
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Error: "ImportError: cannot import name 'app'"
**This means app.main.py has an error.**
**Check:** The file `app\main.py` might have syntax errors or missing imports.

### Error: "Address already in use"
**Fix:**
```powershell
# Kill process on port 8000
$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($p) { Stop-Process -Id $p.OwningProcess -Force }
```

### Error: "ModuleNotFoundError: No module named 'X'"
**Fix:**
```powershell
py -m pip install X
```

## 📋 Manual Start (To See Errors Clearly)

### Start API Manually:
```powershell
cd C:\Users\HP\.cursor
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Watch this window** - it will show the exact error preventing startup.

### Start UI Manually:
```powershell
cd C:\Users\HP\.cursor\sonora
py -m streamlit run ui\demo_app.py --server.port 8501
```

**Watch this window** - it will show the exact error preventing startup.

## 🆘 What to Share

Please share:
1. **Exact error messages** from both PowerShell windows
2. **Screenshot** of the error windows (if possible)
3. **Output of:** `py --version`
4. **Output of:** `py -m pip list | findstr fastapi uvicorn streamlit`

## 💡 Quick Test

To verify Python and imports work:
```powershell
# Test Python
py --version

# Test imports
py -c "import fastapi; print('fastapi OK')"
py -c "import uvicorn; print('uvicorn OK')"
py -c "import streamlit; print('streamlit OK')"

# Test app import
cd C:\Users\HP\.cursor
py -c "from app.main import app; print('app.main OK')"
```

**The last command will show you the exact import error if there is one!**














