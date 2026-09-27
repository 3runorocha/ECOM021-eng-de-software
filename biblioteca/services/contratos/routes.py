from fastapi import APIRouter

from models import Contrato, ContratoCreate
from service import ContratoService


def criar_router(service: ContratoService) -> APIRouter:
    router = APIRouter(prefix="/contratos", tags=["Contratos"])

    @router.post("/", response_model=Contrato, status_code=201)
    def registrar_contrato(dados: ContratoCreate):
        return service.registrar_contrato(dados)

    @router.post("/{contrato_id}/encerrar", response_model=Contrato)
    def encerrar_contrato(contrato_id: int):
        return service.encerrar_contrato(contrato_id)

    @router.get("/", response_model=list[Contrato])
    def listar_contratos(inquilino_id: int = None, status: str = None):
        return service.listar_contratos(inquilino_id, status)

    @router.get("/{contrato_id}", response_model=Contrato)
    def buscar_contrato(contrato_id: int):
        return service.buscar_contrato(contrato_id)

    return router
