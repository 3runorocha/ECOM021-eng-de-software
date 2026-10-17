from typing import Optional

from fastapi import APIRouter, Depends, Header

from models import Pergunta, Resposta, PedidoAviso, Aviso
from agente import Agente


def identificar(
    x_usuario_id: Optional[int] = Header(None),
    x_usuario_tipo: Optional[str] = Header(None),
) -> Optional[dict]:
    if x_usuario_id is None:
        return None
    return {"id": x_usuario_id, "tipo": x_usuario_tipo or ""}


def criar_router(agente: Agente) -> APIRouter:
    router = APIRouter(prefix="/agente", tags=["Agente"])

    @router.post("/perguntar", response_model=Resposta)
    def perguntar(pergunta: Pergunta, chamador=Depends(identificar)):
        return agente.perguntar(pergunta.texto, pergunta.inquilino_id, chamador)

    @router.post("/redigir-aviso", response_model=Aviso)
    def redigir_aviso(pedido: PedidoAviso):
        from agente import MODELO
        return {"mensagem": agente.redigir_aviso(pedido.fatos), "modelo": MODELO}

    @router.get("/status")
    def status():
        return {
            "credencial_configurada": agente.tem_credencial(),
            "ferramentas": ["buscar_imoveis", "detalhar_imovel", "listar_contratos"],
        }

    return router
