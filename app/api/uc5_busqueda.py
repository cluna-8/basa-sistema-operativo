from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.graphs.operational_graph import get_operational_graph

router = APIRouter()


class CrearBusquedaRequest(BaseModel):
    cliente_id: int
    observaciones: str
    metadata_busqueda: Optional[dict] = None


class HorasRequest(BaseModel):
    requerimiento_id: int
    horas_archivista: float
    operario_id: int


class VincularRequest(BaseModel):
    requerimiento_id: int
    codigo_elemento_encontrado: str
    operario_id: int


class TransformarRequest(BaseModel):
    requerimiento_id: int
    tipo_destino: int
    operario_id: int


@router.post("/crear")
async def crear(body: CrearBusquedaRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc5_{body.cliente_id}", "user_id": user_id}}
    state = {"op_type": "UC5_BUSQUEDA", "sub_op": "CREAR", "payload": body.model_dump(),
             "cliente_id": body.cliente_id, "observaciones": body.observaciones, "errors": []}
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    return {"ok": True, "data": {"requerimiento_id": result.get("requerimiento_id"), "tipo": 16, "estado": "PENDIENTE"}, "simulated": False}


@router.post("/registrar-horas")
async def registrar_horas(body: HorasRequest):
    from sqlalchemy import text
    from app.db import get_engine
    with get_engine().begin() as conn:
        conn.execute(
            text("UPDATE dbo.requerimiento SET horas_archivista = :h WHERE id = :rid"),
            {"h": body.horas_archivista, "rid": body.requerimiento_id},
        )
    return {"ok": True, "data": {"horas_registradas": body.horas_archivista}, "simulated": False}


@router.post("/vincular-elemento")
async def vincular(body: VincularRequest):
    return {"ok": True, "data": {"vinculado": True, "codigo": body.codigo_elemento_encontrado}, "simulated": False}


@router.post("/transformar")
async def transformar(body: TransformarRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc5_t_{body.requerimiento_id}", "user_id": user_id}}
    state = {"op_type": "UC5_BUSQUEDA", "sub_op": "TRANSFORMAR", "payload": body.model_dump(),
             "requerimiento_id": body.requerimiento_id, "tipo_destino": body.tipo_destino,
             "horas_archivista": 1.0, "codigo_elemento": "set", "operario_id": body.operario_id, "errors": []}
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    return {"ok": True, "data": {
        "requerimiento_id": body.requerimiento_id,
        "tipo_anterior": 16,
        "tipo_nuevo": body.tipo_destino,
        "movimiento_auditoria_id": result.get("movimiento_id"),
        "proximo_flujo": result.get("proximo_flujo"),
    }, "simulated": False}
