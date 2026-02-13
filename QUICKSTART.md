# CPU-Hardened Swarm: Quick Start Guide

## Prerequisites
1. **Docker Desktop**: Ensure Docker Desktop is running
   - Windows: Check system tray for Docker icon
   - Verify: `docker --version` should return version info

2. **Shared Data Directory**: Will be auto-created at `./shared_data`

## Launch Sequence

### Step 1: Start Docker Desktop
Ensure Docker Desktop is running before proceeding.

### Step 2: Launch the Swarm
```powershell
# From the sonora_repo directory
docker compose up --build
```

### Step 3: Monitor Startup Logs
You should see this synchronized sequence:

```
✅ redis-cache      | Ready to accept connections
✅ sonora-separator | Sonora Health Check: No GPU found. Initializing in CPU-Hardened Mode.
✅ sonora-transcriber | Sonora Health Check: No GPU found. Initializing in CPU-Hardened Mode.
✅ sonora-synthesizer | Sonora Health Check: No GPU found. Initializing in CPU-Hardened Mode.
✅ sonora-ui        | You can now view your Streamlit app in your browser.
                    | Local URL: http://localhost:8501
```

## Verification Tests

### Automated Verification
Run the verification script:
```powershell
python verify_swarm.py
```

This will test:
- ✅ Shared volume accessibility
- ✅ Service health endpoints
- ✅ Transcriber handshake (file → process → result)

### Manual Verification
1. **Open Cockpit**: Navigate to `http://localhost:8501`
2. **Check Services**: All services should show "HEALTHY 🟢" in System Settings
3. **Test Upload**: Upload a small audio file (< 5 seconds)
4. **Verify Shared Data**: Check `./shared_data/` for the uploaded file
5. **Request Processing**: Click "Request Transcription" in the UI
6. **Monitor Logs**: 
   ```powershell
   docker compose logs -f sonora-transcriber
   ```
   Look for: `Sonora Health Check: No GPU found. Initializing in CPU-Hardened Mode.`

## CPU Optimization Tips

### For Faster Testing
The Transcriber service currently uses the full `openai-whisper` package. For CPU-only testing:

1. **Use Smaller Models**: Edit `src/services/transcriber/main.py` to use `base` or `tiny`:
   ```python
   # Instead of default (large)
   model = whisper.load_model("base")  # Much faster on CPU
   ```

2. **Quantization**: Consider using `faster-whisper` for CPU optimization:
   ```txt
   # In src/services/transcriber/requirements.txt
   faster-whisper  # CPU-optimized Whisper
   ```

### Expected Performance (CPU Mode)
- **Tiny Model**: ~2-3x realtime (5s audio = 10-15s processing)
- **Base Model**: ~5-7x realtime (5s audio = 25-35s processing)
- **Small Model**: ~10-15x realtime (5s audio = 50-75s processing)

## Troubleshooting

### Docker Not Found
```
Error: docker: command not found
```
**Solution**: Start Docker Desktop and wait for it to fully initialize.

### Port Already in Use
```
Error: bind: address already in use
```
**Solution**: 
```powershell
# Find and stop conflicting services
netstat -ano | findstr :8501
# Or change ports in docker-compose.yml
```

### Services Not Healthy
```
❌ Transcriber is not reachable
```
**Solution**:
```powershell
# Check service logs
docker compose logs sonora-transcriber

# Restart specific service
docker compose restart sonora-transcriber
```

## Next Steps: GPU Enablement

Once you have NVIDIA drivers installed:

1. **Update Dockerfiles**: Change base image from `python:3.9-slim` to `nvidia/cuda:11.8.0-runtime-ubuntu22.04`
2. **Add GPU Reservation**:
   ```yaml
   # In docker-compose.yml, for each service:
   deploy:
     resources:
       reservations:
         devices:
           - capabilities: [gpu]
   ```
3. **Rebuild**: `docker compose up --build`
4. **Verify**: Logs should show `Device: cuda` instead of `Device: cpu`

## Success Indicators

✅ All services show "healthy" status  
✅ Shared volume contains uploaded files  
✅ Transcriber processes requests without errors  
✅ UI displays CPU-processed results  
✅ No CUDA-related crashes in logs  

**You're ready for production when all indicators are green!**
