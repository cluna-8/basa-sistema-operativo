from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.graphs.query_graph import get_query_agent

router = APIRouter()


class ConsultaRequest(BaseModel):
    thread_id: str
    user_id: str
    mensaje: str


@router.post("/consultar")
async def consultar(body: ConsultaRequest, request: Request):
    rol = getattr(request.state, "rol", "operario")
    if rol != "jefe":
        return JSONResponse(status_code=403, content={"ok": False, "errors": [{"code": "ROL_NO_AUTORIZADO"}]})

    config = {"configurable": {"thread_id": body.thread_id, "user_id": body.user_id}}
    input_msg = {"messages": [{"role": "user", "content": body.mensaje}]}

    agent = get_query_agent()
    result = agent.invoke(input_msg, config=config)
    last_message = result["messages"][-1].content

    escritura_rechazada = any(
        phrase in last_message.lower()
        for phrase in ["solo lectura", "no puedo modificar", "este canal es exclusivamente", "canal es de solo"]
    )

    return {"ok": True, "data": {
        "respuesta": last_message,
        "thread_id": body.thread_id,
        "turno": len(result["messages"]) // 2,
        "escritura_rechazada": escritura_rechazada,
    }}


@router.get("/historial/{thread_id}")
async def historial(thread_id: str, request: Request):
    rol = getattr(request.state, "rol", "operario")
    if rol != "jefe":
        return JSONResponse(status_code=403, content={"ok": False, "errors": [{"code": "ROL_NO_AUTORIZADO"}]})
    return {"ok": True, "data": {"thread_id": thread_id, "mensajes": []}}
