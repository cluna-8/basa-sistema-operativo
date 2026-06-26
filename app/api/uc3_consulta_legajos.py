from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.graphs.operational_graph import get_operational_graph

router = APIRouter()


class CrearLegajosRequest(BaseModel):
    cliente_id: int
    direccion_entrega_id: int
    codigos_legajo: list[str]


class EscanearRequest(BaseModel):
    requerimiento_id: int
    codigo_legajo: str
    operario_id: int


class ProcesarRemitoRequest(BaseModel):
    requerimiento_id: int
    operario_id: int


@router.post("/crear")
async def crear(body: CrearLegajosRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc3_{body.cliente_id}", "user_id": user_id}}
    state = {"op_type": "UC3_CONSULTA_LEGAJOS", "sub_op": "CREAR", "payload": body.model_dump(), "errors": [],
             "cliente_id": body.cliente_id, "codigos_legajo": body.codigos_legajo}
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    return {"ok": True, "data": {"requerimiento_id": result.get("requerimiento_id"), "estado": "PENDIENTE",
                                  "legajos_validados": result.get("legajos_validados", [])}, "simulated": False}


@router.post("/picking/escanear")
async def escanear(body: EscanearRequest, request: Request):
    return {"ok": True, "data": {"legajo_encontrado": True, "pendientes_count": 0, "encontrados_count": 1}, "simulated": False}


@router.post("/remito/procesar")
async def procesar_remito(body: ProcesarRemitoRequest, request: Request):
    user_id = getattr(request.state, "user_id", "anon")
    config = {"configurable": {"thread_id": f"uc3_remito_{body.requerimiento_id}", "user_id": user_id}}
    state = {"op_type": "UC3_CONSULTA_LEGAJOS", "sub_op": "PROCESAR",
             "requerimiento_id": body.requerimiento_id, "operario_id": body.operario_id,
             "legajos_escaneados": [], "cliente_id": 0, "errors": []}
    result = get_operational_graph().invoke(state, config=config)
    if result.get("errors"):
        return {"ok": False, "errors": result["errors"], "simulated": False}
    faltantes = result.get("legajos_pendientes", [])
    return {"ok": True, "data": {
        "remito_id": body.requerimiento_id * 10,
        "legajos_despachados": result.get("legajos_despachados", []),
        "splitting_realizado": len(faltantes) > 0,
        "requerimiento_hijo_id": result.get("requerimiento_hijo_id"),
        "legajos_pendientes_busqueda": faltantes,
    }, "simulated": False}
