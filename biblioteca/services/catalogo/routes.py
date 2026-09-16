from fastapi import APIRouter

from models import Livro, LivroCreate, LivroUpdate
from service import CatalogoService


def criar_router(service: CatalogoService) -> APIRouter:
    router = APIRouter(prefix="/livros", tags=["Catálogo"])

    @router.get("/", response_model=list[Livro])
    def listar_livros(genero: str = None, autor: str = None):
        return service.listar_livros(genero, autor)

    @router.get("/isbn/{isbn}", response_model=Livro)
    def buscar_por_isbn(isbn: str):
        return service.buscar_por_isbn(isbn)

    @router.get("/{livro_id}", response_model=Livro)
    def buscar_livro(livro_id: int):
        return service.buscar_livro(livro_id)

    @router.post("/", response_model=Livro, status_code=201)
    def cadastrar_livro(livro: LivroCreate):
        return service.cadastrar_livro(livro)

    @router.patch("/{livro_id}", response_model=Livro)
    def atualizar_livro(livro_id: int, dados: LivroUpdate):
        return service.atualizar_livro(livro_id, dados)

    @router.delete("/{livro_id}", status_code=204)
    def remover_livro(livro_id: int):
        service.remover_livro(livro_id)

    @router.patch("/{livro_id}/disponibilidade")
    def atualizar_disponibilidade(livro_id: int, delta: int):
        return service.atualizar_disponibilidade(livro_id, delta)

    return router