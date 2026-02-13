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
        
        # 2. Whitelist WebSocket (handled separately or via this if headers supported)
        if "ws" in request.url.path:
             return await call_next(request)

        # 3. Check for API Key
        expected_key = os.getenv("SONORA_API_KEY")
        
        if not expected_key:
            # Dev Mode: Warn but allow if no key configured
            # logger.warning("SECURITY ALERT: No SONORA_API_KEY set. Allowing request.")
            return await call_next(request)
            
        client_key = request.headers.get(API_KEY_NAME)
        
        if not client_key or not secrets.compare_digest(client_key, expected_key):
            logger.warning(f"SECURITY BLOCK: Unauthorized access attempt from {request.client.host}")
            return JSONResponse(
                status_code=403, 
                content={
                    "detail": "Sonora Security Block: Invalid or Missing API Key",
                    "required_header": API_KEY_NAME
                }
            )
            
        return await call_next(request)
