from fastapi import APIRouter

from models import Notificacao, NotificacaoCreate
from service import NotificacaoService


def criar_router(service: NotificacaoService) -> APIRouter:
    router = APIRouter(prefix="/notificacoes", tags=["Notificações"])

    @router.post("/", response_model=Notificacao, status_code=201)
    def criar_notificacao(dados: NotificacaoCreate):
        return service.criar_notificacao(dados)

    @router.get("/usuario/{usuario_id}", response_model=list[Notificacao])
    def listar_por_usuario(usuario_id: int, apenas_nao_lidas: bool = False):
        return service.listar_por_usuario(usuario_id, apenas_nao_lidas)

    @router.patch("/{notificacao_id}/ler", response_model=Notificacao)
    def marcar_como_lida(notificacao_id: int):
        return service.marcar_como_lida(notificacao_id)

    @router.patch("/usuario/{usuario_id}/ler-todas")
    def marcar_todas_como_lidas(usuario_id: int):
        return service.marcar_todas_como_lidas(usuario_id)

    @router.post("/varredura")
    def varredura_automatica():
        return service.executar_varredura()

    return router