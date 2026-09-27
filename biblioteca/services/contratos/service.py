import calendar
from datetime import date

from models import Contrato, ContratoCreate
from repository import ContratoRepository
from clients import ImovelClient
from exceptions import ContratoNaoEncontrado, RegraDeNegocio


def somar_meses(inicio: date, meses: int) -> date:
    """Soma meses preservando o dia, ajustando quando o mes de destino e curto.

    31/01 + 1 mes = 28/02 (ou 29 em ano bissexto). timedelta nao resolve isso
    porque mes nao tem duracao fixa.
    """
    total = inicio.month - 1 + meses
    ano = inicio.year + total // 12
    mes = total % 12 + 1
    dia = min(inicio.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


class ContratoService:

    PRAZO_MESES = 12
    # A multa diaria e proporcional ao aluguel contratado: um dia de atraso
    # custa 1/30 do valor mensal. Substitui o MULTA_POR_DIA fixo de R$ 0,50 do
    # acervo de livros, que nao faz sentido quando o bem vale milhares.
    DIAS_BASE_MULTA = 30

    def __init__(self, repository: ContratoRepository, imoveis: ImovelClient):
        self._repo = repository
        self._imoveis = imoveis

    def registrar_contrato(self, dados: ContratoCreate) -> Contrato:
        imovel = self._imoveis.buscar_imovel(dados.imovel_id)
        if imovel is None:
            raise RegraDeNegocio(f"Imóvel {dados.imovel_id} não encontrado")

        if self._repo.existe_aberto(dados.imovel_id):
            raise RegraDeNegocio(
                f"Imóvel '{imovel['titulo']}' já possui contrato em aberto"
            )

        meses = dados.meses or self.PRAZO_MESES
        inicio = date.today()
        fim_previsto = somar_meses(inicio, meses)

        # Marca o imovel primeiro: e a operacao que pode falhar por disputa com
        # outro contrato. Se o INSERT falhar depois, devolvemos a disponibilidade
        # para nao deixar imovel preso sem contrato.
        self._imoveis.definir_disponibilidade(dados.imovel_id, False)
        try:
            novo_id = self._repo.inserir(
                dados.inquilino_id,
                dados.imovel_id,
                str(inicio),
                str(fim_previsto),
                imovel["valor_mensal"],
            )
        except Exception:
            self._imoveis.definir_disponibilidade(dados.imovel_id, True)
            raise

        return self._repo.buscar_por_id(novo_id)

    def encerrar_contrato(self, contrato_id: int) -> Contrato:
        contrato = self._repo.buscar_por_id(contrato_id)
        if contrato is None:
            raise ContratoNaoEncontrado()
        if contrato.status == "encerrado":
            raise RegraDeNegocio("Contrato já foi encerrado")

        hoje = date.today()
        multa = self.calcular_multa(contrato, hoje)

        self._imoveis.definir_disponibilidade(contrato.imovel_id, True)
        self._repo.encerrar(contrato_id, str(hoje), multa)
        return self._repo.buscar_por_id(contrato_id)

    def calcular_multa(self, contrato: Contrato, data_saida: date) -> float:
        prevista = date.fromisoformat(contrato.data_fim_prevista)
        dias_atraso = max(0, (data_saida - prevista).days)
        if dias_atraso == 0:
            return 0.0
        valor_dia = contrato.valor_mensal / self.DIAS_BASE_MULTA
        return round(dias_atraso * valor_dia, 2)

    def listar_contratos(
        self, inquilino_id: int = None, status: str = None
    ) -> list[Contrato]:
        self._repo.marcar_atrasados()
        return self._repo.listar(inquilino_id, status)

    def buscar_contrato(self, contrato_id: int) -> Contrato:
        contrato = self._repo.buscar_por_id(contrato_id)
        if contrato is None:
            raise ContratoNaoEncontrado()
        return contrato
