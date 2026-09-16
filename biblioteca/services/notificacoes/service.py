from datetime import date

from models import Notificacao, NotificacaoCreate
from repository import NotificacaoRepository
from clients import EmprestimoClient
from exceptions import NotificacaoNaoEncontrada


class NotificacaoService:

    DIAS_ALERTA_PRAZO = 2
    MULTA_POR_DIA = 0.50
    TIPOS_AUTOMATICOS = ("atraso", "prazo_proximo")

    def __init__(
        self, repository: NotificacaoRepository, emprestimos: EmprestimoClient
    ):
        self._repo = repository
        self._emprestimos = emprestimos

    def criar_notificacao(self, dados: NotificacaoCreate) -> Notificacao:
        novo_id = self._repo.inserir(dados)
        return self._repo.buscar_por_id(novo_id)

    def listar_por_usuario(
        self, usuario_id: int, apenas_nao_lidas: bool = False
    ) -> list[Notificacao]:
        return self._repo.listar_por_usuario(usuario_id, apenas_nao_lidas)

    def marcar_como_lida(self, notificacao_id: int) -> Notificacao:
        notificacao = self._repo.buscar_por_id(notificacao_id)
        if notificacao is None:
            raise NotificacaoNaoEncontrada()
        self._repo.marcar_como_lida(notificacao_id)
        return self._repo.buscar_por_id(notificacao_id)

    def marcar_todas_como_lidas(self, usuario_id: int) -> dict:
        self._repo.marcar_todas_como_lidas(usuario_id)
        return {
            "mensagem": (
                f"Todas as notificações do usuário {usuario_id} "
                "marcadas como lidas"
            )
        }

    def executar_varredura(self) -> dict:
        emprestimos = self._emprestimos.listar_emprestimos()
        hoje = date.today()
        geradas = 0

        for emp in emprestimos:
            if emp["status"] == "devolvido":
                continue

            usuario_id = emp["usuario_id"]
            livro_id = emp["livro_id"]
            prevista = date.fromisoformat(emp["data_devolucao_prevista"])
            dias_restantes = (prevista - hoje).days

            if self._repo.existe_nao_lida(
                usuario_id, livro_id, self.TIPOS_AUTOMATICOS
            ):
                continue

            notificacao = self._montar_notificacao(
                emp, usuario_id, livro_id, dias_restantes
            )
            if notificacao is not None:
                self._repo.inserir(notificacao)
                geradas += 1

        return {
            "mensagem": f"Varredura concluída. {geradas} notificação(ões) gerada(s)."
        }

    def _montar_notificacao(
        self, emp: dict, usuario_id: int, livro_id: int, dias_restantes: int
    ) -> NotificacaoCreate | None:
        if emp["status"] == "atrasado":
            dias_atraso = abs(dias_restantes)
            multa = round(dias_atraso * self.MULTA_POR_DIA, 2)
            return NotificacaoCreate(
                usuario_id=usuario_id,
                tipo="atraso",
                mensagem=(
                    f"Seu empréstimo do livro ID {livro_id} está atrasado há "
                    f"{dias_atraso} dia(s). Multa acumulada: R$ {multa:.2f}."
                ),
                livro_id=livro_id,
            )

        if 0 <= dias_restantes <= self.DIAS_ALERTA_PRAZO:
            return NotificacaoCreate(
                usuario_id=usuario_id,
                tipo="prazo_proximo",
                mensagem=(
                    f"Atenção! O prazo de devolução do livro ID {livro_id} "
                    f"vence em {dias_restantes} dia(s) "
                    f"({emp['data_devolucao_prevista']})."
                ),
                livro_id=livro_id,
            )

        return None