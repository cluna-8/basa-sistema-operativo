from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.graphs.operational_graph import get_operational_graph

router = APIRouter()


class AsignarRequest(BaseModel):
    codigo_caja: str
    codigo_posicion: str
    operario_id: int


@router.post("/asignar")
async def asignar_ubicacion(body: AsignarRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc1_{body.operario_id}", "user_id": user_id}}
    state = {
        "op_type": "UC1_UBICACION",
        "payload": body.model_dump(),
        "errors": [],
    }
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    return {
        "ok": True,
        "data": {
            "elemento_id": result.get("elemento_id"),
            "posicion_id": result.get("posicion_id"),
            "estado_posicion": "OCUPADO",
            "movimiento_id": result.get("movimiento_id"),
        },
        "simulated": False,
    }


@router.get("/posicion/{codigo_modulo}")
async def get_posicion(codigo_modulo: str):
    from sqlalchemy import text
    from app.db import get_engine
    with get_engine().connect() as conn:
        row = conn.execute(
            text("SELECT id, estado, estanteria, codigo_modulo FROM dbo.posicion WHERE codigo_modulo = :c"),
            {"c": codigo_modulo},
        ).fetchone()
    if not row:
        return {"ok": False, "errors": [{"code": "POSICION_NO_ENCONTRADA"}]}
    return {
        "ok": True,
        "data": {
            "posicion_id": row.id,
            "estado": row.estado,
            "estanteria": row.estanteria,
            "codigo_modulo": row.codigo_modulo,
        },
    }
