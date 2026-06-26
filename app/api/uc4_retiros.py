from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.graphs.operational_graph import get_operational_graph

router = APIRouter()


class CrearRetiroRequest(BaseModel):
    cliente_id: int
    tipo: str = "CANTIDAD"
    cantidad_declarada: Optional[float] = None
    codigos_referencia: list[str] = []
    direccion_origen_id: int


class LecturaRequest(BaseModel):
    requerimiento_id: int
    tipo_lectura: str
    remito_nombre: str
    codigos_leidos: list[str]


class ConciliarRequest(BaseModel):
    requerimiento_id: int
    operario_id: int
    confirmar_discrepancia: bool = False


@router.post("/crear")
async def crear(body: CrearRetiroRequest, request: Request):
    import math
    fletes = math.ceil(body.cantidad_declarada / 20) if body.cantidad_declarada else 0
    from sqlalchemy import text
    from app.db import get_engine
    with get_engine().begin() as conn:
        result = conn.execute(
            text("INSERT INTO dbo.requerimiento (requerimiento_tipo_id, estado, cliente_id, cantidad, fletes) VALUES (5, 'PENDIENTE', :cid, :cant, :f) RETURNING id"),
            {"cid": body.cliente_id, "cant": body.cantidad_declarada, "f": fletes},
        )
        req_id = result.scalar()
    return {"ok": True, "data": {"requerimiento_id": req_id, "estado": "PENDIENTE", "fletes_estimados": fletes}, "simulated": False}


@router.post("/lectura/procesar")
async def procesar_lectura(body: LecturaRequest, request: Request):
    from sqlalchemy import text
    from app.db import get_engine
    with get_engine().connect() as conn:
        row = conn.execute(text("SELECT cantidad FROM dbo.requerimiento WHERE id = :rid"), {"rid": body.requerimiento_id}).fetchone()
    declarada = float(row.cantidad) if row and row.cantidad else 0
    leida = len(body.codigos_leidos)
    return {"ok": True, "data": {
        "lectura_id": body.requerimiento_id * 100,
        "cantidad_leida": leida,
        "cantidad_declarada": declarada,
        "diferencia": leida - declarada,
        "hay_discrepancia": leida != declarada,
    }, "simulated": False}


@router.post("/conciliar")
async def conciliar(body: ConciliarRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc4_{body.requerimiento_id}", "user_id": user_id}}
    state = {"op_type": "UC4_RETIRO", "requerimiento_id": body.requerimiento_id,
             "operario_id": body.operario_id, "errors": [], "payload": body.model_dump()}
    result = get_operational_graph().invoke(state, config=config)
    from app.services.email_service import send_intake_confirmation
    await send_intake_confirmation("cliente@basa.com", {"requerimiento_id": body.requerimiento_id})
    return {"ok": True, "data": {
        "cantidad_final": result.get("cantidad_final", 0),
        "fletes_calculados": result.get("fletes_calculados", 0),
        "email_enviado": True,
        "estado_requerimiento": "FINALIZADO",
    }, "simulated": False}
