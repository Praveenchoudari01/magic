import re
import hmac
import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .db import get_connection  # your DB connection function

# Only allow simple numeric values to avoid SQL injection
SAFE_HEADER_REGEX = re.compile(r"^[0-9]+$")

# Global static secret key (same for all devices)
# GLOBAL_DEVICE_SECRET = "MY_STATIC_SECRET_2025"

# Paths that don't require auth
OPEN_PATHS = {"/validate-code"}

class HeaderAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Skip auth for certain paths
        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        # Extract headers
        client_id = request.headers.get("client-id")
        device_id = request.headers.get("device-id")
        # signature = request.headers.get("signature")

        # Check missing headers
        # if not client_id or not device_id or not signature:
        #     return JSONResponse(
        #         status_code=401,
        #         content={"status": "unauthorized", "message": "Missing authentication headers"}
        #     )

        # Validate header formats
        if not SAFE_HEADER_REGEX.match(client_id) or not SAFE_HEADER_REGEX.match(device_id):
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Invalid header format"}
            )

        # # HMAC signature validation
        # message = f"{client_id}{device_id}"
        # server_signature = hmac.new(
        #     GLOBAL_DEVICE_SECRET.encode(),
        #     message.encode(),
        #     hashlib.sha256
        # ).hexdigest()

        # # Use secure compare to prevent timing attacks
        # if not hmac.compare_digest(server_signature, signature):
        #     return JSONResponse(
        #         status_code=401,
        #         content={"status": "unauthorized", "message": "Invalid signature"}
        #     )

        # Optional: Validate in database
        try:
            db = get_connection()
            cursor = db.cursor()

            query = """
                SELECT device_id 
                FROM vr_device
                WHERE client_id = %s AND device_id = %s
            """

            cursor.execute(query, (client_id, device_id))
            record = cursor.fetchone()

            if not record:
                return JSONResponse(
                    status_code=401,
                    content={"status": "unauthorized", "message": "Invalid client_id or device_id"}
                )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Internal server error"}
            )

        # All checks passed → allow endpoint execution
        response = await call_next(request)
        return response
