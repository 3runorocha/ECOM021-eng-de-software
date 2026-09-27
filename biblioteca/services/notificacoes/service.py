from datetime import date

from models import Notificacao, NotificacaoCreate
from repository import NotificacaoRepository
from clients import ContratoClient
from exceptions import NotificacaoNaoEncontrada


class NotificacaoService:

    DIAS_ALERTA_PRAZO = 2
    # Mesma base do servico de contratos: um dia de atraso custa 1/30 do
    # aluguel. O valor sai do proprio contrato, entao aqui nao ha constante de
    # multa duplicada -- antes havia um MULTA_POR_DIA = 0.50 repetido.
    DIAS_BASE_MULTA = 30
    TIPOS_AUTOMATICOS = ("atraso", "prazo_proximo")

    def __init__(
        self, repository: NotificacaoRepository, contratos: ContratoClient
    ):
        self._repo = repository
        self._contratos = contratos

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
        contratos = self._contratos.listar_contratos()
        hoje = date.today()
        geradas = 0

        for contrato in contratos:
            if contrato["status"] == "encerrado":
                continue

            inquilino_id = contrato["inquilino_id"]
            imovel_id = contrato["imovel_id"]
            prevista = date.fromisoformat(contrato["data_fim_prevista"])
            dias_restantes = (prevista - hoje).days

            if self._repo.existe_nao_lida(
                inquilino_id, imovel_id, self.TIPOS_AUTOMATICOS
            ):
                continue

            notificacao = self._montar_notificacao(
                contrato, inquilino_id, imovel_id, dias_restantes
            )
            if notificacao is not None:
                self._repo.inserir(notificacao)
                geradas += 1

        return {
            "mensagem": f"Varredura concluída. {geradas} notificação(ões) gerada(s)."
        }

    def _montar_notificacao(
        self, contrato: dict, inquilino_id: int, imovel_id: int, dias_restantes: int
    ) -> NotificacaoCreate | None:
        if contrato["status"] == "atrasado":
            dias_atraso = abs(dias_restantes)
            valor_dia = contrato["valor_mensal"] / self.DIAS_BASE_MULTA
            multa = round(dias_atraso * valor_dia, 2)
            return NotificacaoCreate(
                usuario_id=inquilino_id,
                tipo="atraso",
                mensagem=(
                    f"O contrato do imóvel ID {imovel_id} venceu há "
                    f"{dias_atraso} dia(s). Multa acumulada: R$ {multa:.2f}."
                ),
                imovel_id=imovel_id,
            )

        if 0 <= dias_restantes <= self.DIAS_ALERTA_PRAZO:
            return NotificacaoCreate(
                usuario_id=inquilino_id,
                tipo="prazo_proximo",
                mensagem=(
                    f"Atenção! O contrato do imóvel ID {imovel_id} "
                    f"vence em {dias_restantes} dia(s) "
                    f"({contrato['data_fim_prevista']})."
                ),
                imovel_id=imovel_id,
            )

        return None
