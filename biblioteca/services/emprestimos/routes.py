from fastapi import APIRouter

from models import Emprestimo, EmprestimoCreate
from service import EmprestimoService


def criar_router(service: EmprestimoService) -> APIRouter:
    router = APIRouter(prefix="/emprestimos", tags=["Empréstimos"])

    @router.post("/", response_model=Emprestimo, status_code=201)
    def registrar_emprestimo(dados: EmprestimoCreate):
        return service.registrar_emprestimo(dados)

    @router.post("/{emprestimo_id}/devolver", response_model=Emprestimo)
    def registrar_devolucao(emprestimo_id: int):
        return service.registrar_devolucao(emprestimo_id)

    @router.get("/", response_model=list[Emprestimo])
    def listar_emprestimos(usuario_id: int = None, status: str = None):
        return service.listar_emprestimos(usuario_id, status)

    @router.get("/{emprestimo_id}", response_model=Emprestimo)
    def buscar_emprestimo(emprestimo_id: int):
        return service.buscar_emprestimo(emprestimo_id)

    return router