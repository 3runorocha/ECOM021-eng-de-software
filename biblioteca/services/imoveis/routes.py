from fastapi import APIRouter

from models import Imovel, ImovelCreate, ImovelUpdate
from service import ImovelService


def criar_router(service: ImovelService) -> APIRouter:
    router = APIRouter(prefix="/imoveis", tags=["Imóveis"])

    @router.get("/", response_model=list[Imovel])
    def listar_imoveis(
        cidade: str = None,
        tipo: str = None,
        quartos_min: int = None,
        valor_min: float = None,
        valor_max: float = None,
        disponivel: bool = None,
    ):
        return service.listar_imoveis(
            cidade=cidade, tipo=tipo, quartos_min=quartos_min,
            valor_min=valor_min, valor_max=valor_max, disponivel=disponivel,
        )

    @router.get("/{imovel_id}", response_model=Imovel)
    def buscar_imovel(imovel_id: int):
        return service.buscar_imovel(imovel_id)

    @router.post("/", response_model=Imovel, status_code=201)
    def cadastrar_imovel(imovel: ImovelCreate):
        return service.cadastrar_imovel(imovel)

    @router.patch("/{imovel_id}", response_model=Imovel)
    def atualizar_imovel(imovel_id: int, dados: ImovelUpdate):
        return service.atualizar_imovel(imovel_id, dados)

    @router.delete("/{imovel_id}", status_code=204)
    def remover_imovel(imovel_id: int):
        service.remover_imovel(imovel_id)

    @router.patch("/{imovel_id}/disponibilidade")
    def definir_disponibilidade(imovel_id: int, disponivel: bool):
        return service.definir_disponibilidade(imovel_id, disponivel)

    return router
