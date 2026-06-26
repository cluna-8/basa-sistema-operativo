import os
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

SECRET = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/api/auth/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return JSONResponse(status_code=401, content={"ok": False, "errors": [{"code": "UNAUTHORIZED"}]})

        try:
            payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            request.state.user_id = payload.get("sub", "")
            request.state.rol = payload.get("rol", "operario")
        except JWTError:
            return JSONResponse(status_code=401, content={"ok": False, "errors": [{"code": "TOKEN_INVALID"}]})

        return await call_next(request)
