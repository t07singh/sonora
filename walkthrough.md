# 🔬 Sonora Swarm Diagnostic Walkthrough

This document outlines the verification steps for the **Infrastructure Alignment** update. Follow these steps to ensure the sequential flush and file handshake protocols are operating correctly.

## 1. Orchestration Start
Ensure Docker Desktop is running, then launch the swarm:
```cmd
docker compose up -d --build
```

## 2. Node Integrity Check (Host Verification)
Verify each microservice is responsive and reporting its hardware context:

| Service | Endpoint | Port | Expected Response |
|---------|----------|------|-------------------|
| **Separator** | `curl http://localhost:8000/health` | 8000 | `{"status": "healthy", ...}` |
| **Transcriber** | `curl http://localhost:8001/health` | 8001 | `{"status": "healthy", "device": "cpu"}` |
| **Synthesizer** | `curl http://localhost:8002/health` | 8002 | `{"status": "healthy", ...}` |
| **Lip-Sync** | `curl http://localhost:8004/health` | 8004 | `{"status": "healthy", "vram_limit": "2GB_Optimized"}` |

## 3. Shared Data Handshake Audit
All services share the `./shared_data` directory. You can monitor the atomic handshake in real-time from your host machine:

1.  **Upload a file** via the UI at `http://localhost:8501`.
2.  **Verify visibility**: Check if the file appears in `./shared_data/uploads/`.
3.  **Monitor logs**: Run `docker compose logs -f sonora-transcriber` to see the "Ingestion Engine" process the file.

## 4. Sequential Flush Protocol (VRAM Guard)
To verify the `HardwareLock` is preventing concurrent OOM crashes:
1.  Initiate a **Synthesis** task in the UI.
2.  Immediately attempt a **Lip-Sync** task.
3.  Check the logs: You should see the second task wait with `🔒 HardwareLock ACQUIRED` until the first releases with `🔓 HardwareLock RELEASED`.

## 5. Troubleshooting
If you see a `404 Not Found` or `Connection Refused`:
- Check if the bind mount `./shared_data` exists in your project root.
- Ensure no other processes (like a standalone Sonora server) are occupying ports 8000-8004.
