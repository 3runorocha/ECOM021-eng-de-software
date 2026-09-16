from models import Livro, LivroCreate, LivroUpdate
from repository import LivroRepository
from exceptions import LivroNaoEncontrado, RegraDeNegocio


class CatalogoService:

    def __init__(self, repository: LivroRepository):
        self._repo = repository

    def listar_livros(self, genero: str = None, autor: str = None) -> list[Livro]:
        return self._repo.listar(genero, autor)

    def buscar_livro(self, livro_id: int) -> Livro:
        livro = self._repo.buscar_por_id(livro_id)
        if livro is None:
            raise LivroNaoEncontrado()
        return livro

    def buscar_por_isbn(self, isbn: str) -> Livro:
        livro = self._repo.buscar_por_isbn(isbn)
        if livro is None:
            raise LivroNaoEncontrado()
        return livro

    def cadastrar_livro(self, dados: LivroCreate) -> Livro:
        novo_id = self._repo.inserir(dados, dados.quantidade_total)
        return self._repo.buscar_por_id(novo_id)

    def atualizar_livro(self, livro_id: int, dados: LivroUpdate) -> Livro:
        atual = self._repo.buscar_por_id(livro_id)
        if atual is None:
            raise LivroNaoEncontrado()

        campos = dados.model_dump(exclude_none=True)
        if not campos:
            return atual

        self._repo.atualizar(livro_id, campos)
        return self._repo.buscar_por_id(livro_id)

    def remover_livro(self, livro_id: int) -> None:
        atual = self._repo.buscar_por_id(livro_id)
        if atual is None:
            raise LivroNaoEncontrado()
        self._repo.remover(livro_id)

    def atualizar_disponibilidade(self, livro_id: int, delta: int) -> dict:
        livro = self._repo.buscar_por_id(livro_id)
        if livro is None:
            raise LivroNaoEncontrado()

        nova_qtd = livro.quantidade_disponivel + delta
        if nova_qtd < 0:
            raise RegraDeNegocio("Nenhum exemplar disponível")
        if nova_qtd > livro.quantidade_total:
            raise RegraDeNegocio("Quantidade excede o total do acervo")

        self._repo.atualizar(livro_id, {"quantidade_disponivel": nova_qtd})
        return {"livro_id": livro_id, "quantidade_disponivel": nova_qtd}