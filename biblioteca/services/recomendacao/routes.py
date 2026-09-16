from fastapi import APIRouter

from models import LivroRecomendado, PerfilUsuario
from service import RecomendacaoService


def criar_router(service: RecomendacaoService) -> APIRouter:
    router = APIRouter(prefix="/recomendacao", tags=["Recomendação"])

    @router.get("/perfil/{usuario_id}", response_model=PerfilUsuario)
    def obter_perfil(usuario_id: int):
        return service.obter_perfil(usuario_id)

    @router.get("/{usuario_id}", response_model=list[LivroRecomendado])
    def recomendar(usuario_id: int, limite: int = 5):
        return service.recomendar(usuario_id, limite)

    return router