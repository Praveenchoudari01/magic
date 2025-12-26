import re
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .db import get_connection

UUID_REGEX = re.compile(
    r'^[0-9a-fA-F]{8}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{12}$'
)

# Public endpoints (no auth)
OPEN_PATHS = {"/validate-code"}

# Protected endpoints (auth required)
PROTECTED_PATHS = {
    "/operators",
    "/processes",
    "/operator-stats",
}

class HeaderAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        path = request.url.path

        # 🚫 Block everything else
        if path not in OPEN_PATHS and path not in PROTECTED_PATHS:
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"}
            )

        # 🔓 Open endpoint
        if path in OPEN_PATHS:
            return await call_next(request)

        # 🔐 Auth required below
        api_key = request.headers.get("api-key")

        if not api_key or ":" not in api_key:
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Missing or invalid api-key"}
            )

        try:
            client_id, device_id = api_key.split(":", 1)
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Invalid api-key format"}
            )

        # Validate UUID format
        if not UUID_REGEX.match(client_id) or not UUID_REGEX.match(device_id):
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Invalid api-key format"}
            )

        try:
            db = get_connection()
            cursor = db.cursor()

            cursor.execute(
                """
                SELECT 1
                FROM vr_device
                WHERE client_id = %s AND device_id = %s AND is_active = 1
                """,
                (client_id, device_id)
            )

            if not cursor.fetchone():
                return JSONResponse(
                    status_code=401,
                    content={"status": "unauthorized", "message": "Invalid credentials"}
                )

        except Exception:
            # 🧠 Never expose DB errors
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Internal server error"}
            )

        return await call_next(request)
