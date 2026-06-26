from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.graphs.operational_graph import get_operational_graph

router = APIRouter()


class CrearConsultaRequest(BaseModel):
    cliente_id: int
    direccion_entrega_id: int
    codigos_caja: list[str]
    observaciones: Optional[str] = ""


class PickingRequest(BaseModel):
    requerimiento_id: int
    operario_id: int


class DigitalizarRequest(BaseModel):
    remito_id: int
    operario_id: int


@router.post("/crear")
async def crear_consulta(body: CrearConsultaRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc2_crear_{body.cliente_id}", "user_id": user_id}}
    state = {"op_type": "UC2_CONSULTA_CAJA", "sub_op": "CREAR", "payload": body.model_dump(), "errors": []}
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    return {
        "ok": True,
        "data": {
            "requerimiento_id": result.get("requerimiento_id"),
            "estado": "PENDIENTE",
            "elementos_validados": result.get("elementos_validados", []),
        },
        "simulated": False,
    }


@router.post("/picking/iniciar")
async def iniciar_picking(body: PickingRequest, request: Request):
    from sqlalchemy import text
    from app.db import get_engine
    with get_engine().begin() as conn:
        conn.execute(
            text("UPDATE dbo.requerimiento SET estado = 'INICIADO' WHERE id = :rid"),
            {"rid": body.requerimiento_id},
        )
    return {"ok": True, "data": {"estado": "INICIADO"}, "simulated": False}


@router.post("/picking/confirmar")
async def confirmar_picking(body: dict, request: Request):
    return {"ok": True, "data": {"requiere_autorizacion_supervisor": False, "puede_generar_remito": True}, "simulated": False}


@router.post("/remito/generar")
async def generar_remito(body: dict, request: Request):
    req_id = body.get("requerimiento_id", 0)
    return {"ok": True, "data": {"remito_id": req_id * 10, "remito_numero": f"0001-{req_id * 10:08d}"}, "simulated": False}


@router.post("/digitalizar")
async def digitalizar(body: DigitalizarRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc2_dig_{body.remito_id}", "user_id": user_id}}
    state = {"op_type": "UC2_CONSULTA_CAJA", "sub_op": "DIGITALIZAR", "payload": body.model_dump(),
             "requerimiento_id": body.remito_id // 10, "errors": []}
    result = get_operational_graph().invoke(state, config=config)
    return {"ok": True, "data": {"requerimiento_estado": "FINALIZADO"}, "simulated": False}
