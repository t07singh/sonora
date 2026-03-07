from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import os
import logging
import secrets

logger = logging.getLogger("sonora.security")

API_KEY_NAME = "X-Sonora-Key"

class SonoraAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Whitelist Health Checks and Docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/"]:
            return await call_next(request)
        
        # 2. Whitelist WebSocket
        if "ws" in request.url.path:
             return await call_next(request)

        # 3. Check for API Key with fallback and stripping
        expected_key = os.getenv("SONORA_API_KEY", "admin123").strip()
        client_key = request.headers.get(API_KEY_NAME, "").strip()
        
        # Diagnostic Log (Masked)
        if not expected_key:
             logger.warning("SECURITY ALERT: SONORA_API_KEY is empty. Hardening to 'admin123'.")
             expected_key = "admin123"

        if not secrets.compare_digest(client_key, expected_key):
            logger.warning(f"SECURITY BLOCK: Unauthorized access attempt. Expected starts with {expected_key[:2]}..., got {client_key[:2]}...")
            return JSONResponse(
                status_code=403, 
                content={
                    "detail": "Sonora Security Block: Invalid or Missing API Key",
                    "required_header": API_KEY_NAME,
                    "debug_hint": "Check SONORA_API_KEY in .env and Ensure UI/API are synced."
                }
            )
            
        return await call_next(request)
