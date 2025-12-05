import re
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .db import get_connection# your db connection function


# Only allow simple numeric values to avoid SQL injection
SAFE_HEADER_REGEX = re.compile(r"^[0-9]+$")

class HeaderAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Extract headers
        client_id = request.headers.get("client-id")
        device_id = request.headers.get("device-id")

        # print("client and device id from the middleware")
        # print(client_id)
        # print(device_id)
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

        # Validate in database
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
                content={"status": "error", "message": str(e)}
            )

        # All checks passed → allow endpoint execution
        response = await call_next(request)
        return response
