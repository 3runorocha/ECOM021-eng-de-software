from datetime import date, timedelta

from models import Emprestimo, EmprestimoCreate
from repository import EmprestimoRepository
from clients import CatalogoClient
from exceptions import EmprestimoNaoEncontrado, RegraDeNegocio


class EmprestimoService:

    PRAZO_DIAS = 14
    MULTA_POR_DIA = 0.50

    def __init__(self, repository: EmprestimoRepository, catalogo: CatalogoClient):
        self._repo = repository
        self._catalogo = catalogo

    def registrar_emprestimo(self, dados: EmprestimoCreate) -> Emprestimo:
        if self._repo.existe_ativo(dados.usuario_id, dados.livro_id):
            raise RegraDeNegocio("Usuário já possui este livro emprestado")

        self._catalogo.atualizar_disponibilidade(dados.livro_id, -1)

        hoje = date.today()
        prevista = hoje + timedelta(days=self.PRAZO_DIAS)
        novo_id = self._repo.inserir(
            dados.usuario_id, dados.livro_id, str(hoje), str(prevista)
        )
        return self._repo.buscar_por_id(novo_id)

    def registrar_devolucao(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self._repo.buscar_por_id(emprestimo_id)
        if emprestimo is None:
            raise EmprestimoNaoEncontrado()
        if emprestimo.status == "devolvido":
            raise RegraDeNegocio("Livro já foi devolvido")

        hoje = date.today()
        prevista = date.fromisoformat(emprestimo.data_devolucao_prevista)
        atraso = max(0, (hoje - prevista).days)
        multa = round(atraso * self.MULTA_POR_DIA, 2)

        self._catalogo.atualizar_disponibilidade(emprestimo.livro_id, +1)
        self._repo.registrar_devolucao(emprestimo_id, str(hoje), multa)
        return self._repo.buscar_por_id(emprestimo_id)

    def listar_emprestimos(
        self, usuario_id: int = None, status: str = None
    ) -> list[Emprestimo]:
        self._repo.marcar_atrasados()
        return self._repo.listar(usuario_id, status)

    def buscar_emprestimo(self, emprestimo_id: int) -> Emprestimo:
        emprestimo = self._repo.buscar_por_id(emprestimo_id)
        if emprestimo is None:
            raise EmprestimoNaoEncontrado()
        return emprestimo