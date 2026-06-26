import os
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from jose import jwt

from app.memory import get_checkpointer, get_store
from app.middleware.error_handler import register_error_handlers
from app.api import uc1_ubicacion, uc2_consulta_caja, uc3_consulta_legajos
from app.api import uc4_retiros, uc5_busqueda, jefes

DEV_USERS = {
    "admin":    {"password": "admin123",   "rol": "jefe"},
    "operario": {"password": "basa2024",   "rol": "operario"},
    "jefe":     {"password": "jefe2024",   "rol": "jefe"},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_checkpointer()
    get_store()
    yield


app = FastAPI(
    title="BASA Sistema Operativo",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(uc1_ubicacion.router, prefix="/api/v1/ubicacion", tags=["UC1 Ubicación"])
app.include_router(uc2_consulta_caja.router, prefix="/api/v1/consulta-caja", tags=["UC2 Consulta Caja"])
app.include_router(uc3_consulta_legajos.router, prefix="/api/v1/consulta-legajos", tags=["UC3 Legajos"])
app.include_router(uc4_retiros.router, prefix="/api/v1/retiros", tags=["UC4 Retiros"])
app.include_router(uc5_busqueda.router, prefix="/api/v1/busqueda", tags=["UC5 Búsqueda"])
app.include_router(jefes.router, prefix="/api/v1/jefes", tags=["UC6 Jefes"])


@app.post("/api/auth/login")
async def auth_login(username: str = Form(...), password: str = Form(...)):
    user = DEV_USERS.get(username)
    if not user or user["password"] != password:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Credenciales incorrectas"})
    token = jwt.encode(
        {"sub": username, "rol": user["rol"]},
        os.getenv("JWT_SECRET", "changeme"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/bundle")
async def get_bundle():
    from datetime import datetime
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": "1.0.0",
        "project": {
            "id": "basa-sistema-operativo",
            "name": "BASA Argentina",
            "summary": "Sistema Operativo Integral · Banco de Archivos S.A.",
        },
        "kpis": [
            {"id": "uc-completados", "label": "UCs Implementados", "value": 6, "trend": "up", "status": "ok"},
            {"id": "servicios", "label": "Servicios Docker", "value": 4, "trend": "neutral", "status": "ok"},
            {"id": "endpoints", "label": "Endpoints API", "value": 18, "trend": "up", "status": "ok"},
            {"id": "entidades", "label": "Entidades DB", "value": 7, "trend": "neutral", "status": "ok"},
        ],
        "use_cases": [
            {"id": "uc1", "title": "UC1 · Ubicación de Cajas en Planta", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
            {"id": "uc2", "title": "UC2 · Consulta Normal de Caja", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
            {"id": "uc3", "title": "UC3 · Consulta de Legajos (Splitting)", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
            {"id": "uc4", "title": "UC4 · Retiros por Cantidad / Referencia", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
            {"id": "uc5", "title": "UC5 · Trámite de Búsqueda / Investigación", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
            {"id": "uc6", "title": "UC6 · Consulta Conversacional para Jefes (IA)", "status": "done", "deadline": None, "deadline_overdue": False, "progress": {"completed": 1, "total": 1, "percentage": 100}, "effort": None, "deliverables": [], "component_ids": []},
        ],
        "timeline": [],
        "components": [],
        "changes": [],
        "notification_log": [],
        "chat_threads": {},
        "alerts": [],
    }


@app.get("/health")
async def health():
    import redis as redis_lib, os
    from app.db import get_engine
    try:
        with get_engine().connect():
            pass
        redis_lib.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")).ping()
        return {"ok": True, "postgres": "up", "redis": "up"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
