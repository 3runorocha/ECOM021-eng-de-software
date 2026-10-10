from fastapi import APIRouter

from models import Pergunta, Resposta
from agente import Agente


def criar_router(agente: Agente) -> APIRouter:
    router = APIRouter(prefix="/agente", tags=["Agente"])

    @router.post("/perguntar", response_model=Resposta)
    def perguntar(pergunta: Pergunta):
        return agente.perguntar(pergunta.texto, pergunta.inquilino_id)

    @router.get("/status")
    def status():
        return {
            "credencial_configurada": agente.tem_credencial(),
            "ferramentas": ["buscar_imoveis", "detalhar_imovel", "listar_contratos"],
        }

    return router
