import re
import hmac
import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .db import get_connection

# Only allow simple numeric values to avoid SQL injection
SAFE_HEADER_REGEX = re.compile(
    r'^[0-9a-fA-F]{8}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{4}-'
    r'[0-9a-fA-F]{12}$'
)


# Paths that don't require auth
OPEN_PATHS = {"/validate-code"}

class HeaderAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Skip auth for certain paths
        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        # Extract headers
        api_key = request.headers.get("api-key")
        client_id, device_id = api_key.split(":")

        # Check missing headers
        if not client_id or not device_id:
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Missing authentication headers"}
            )

        # Validate header formats
        if not SAFE_HEADER_REGEX.match(client_id) or not SAFE_HEADER_REGEX.match(device_id):
            return JSONResponse(
                status_code=401,
                content={"status": "unauthorized", "message": "Invalid header format"}
            )

        client_id = client_id
        device_id = device_id
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

        response = await call_next(request)
        return response
