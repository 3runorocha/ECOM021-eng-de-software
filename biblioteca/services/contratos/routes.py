from typing import Optional

from fastapi import APIRouter, Depends, Header

from models import Chamador, Contrato, ContratoCreate
from service import ContratoService


def identificar(
    x_usuario_id: Optional[int] = Header(None),
    x_usuario_tipo: Optional[str] = Header(None),
) -> Optional[Chamador]:
    if x_usuario_id is None:
        return None
    return Chamador(id=x_usuario_id, tipo=x_usuario_tipo or "")


def criar_router(service: ContratoService) -> APIRouter:
    router = APIRouter(prefix="/contratos", tags=["Contratos"])

    @router.post("/", response_model=Contrato, status_code=201)
    def registrar_contrato(dados: ContratoCreate, chamador=Depends(identificar)):
        return service.registrar_contrato(dados, chamador)

    @router.post("/{contrato_id}/encerrar", response_model=Contrato)
    def encerrar_contrato(contrato_id: int, chamador=Depends(identificar)):
        return service.encerrar_contrato(contrato_id, chamador)

    @router.get("/", response_model=list[Contrato])
    def listar_contratos(
        inquilino_id: int = None, status: str = None, chamador=Depends(identificar)
    ):
        return service.listar_contratos(inquilino_id, status, chamador)

    @router.get("/{contrato_id}", response_model=Contrato)
    def buscar_contrato(contrato_id: int, chamador=Depends(identificar)):
        return service.buscar_contrato(contrato_id, chamador)

    return router
