"""Serviço de contratos: prazo, multa, regra de um contrato por imóvel e a
compensação quando o INSERT falha depois de ocupar o imóvel."""
from datetime import date

import pytest

from conftest import carregar

modelos, servico_mod, excecoes = carregar(
    "contratos", "models", "service", "exceptions"
)

Contrato = modelos.Contrato
ContratoCreate = modelos.ContratoCreate
ContratoService = servico_mod.ContratoService
somar_meses = servico_mod.somar_meses
ContratoNaoEncontrado = excecoes.ContratoNaoEncontrado
RegraDeNegocio = excecoes.RegraDeNegocio


def contrato(id=1, imovel_id=5, inquilino_id=1, inicio="2025-01-10",
             fim="2026-01-10", fim_real=None, valor=3000.0, status="ativo",
             multa=0.0):
    return Contrato(
        id=id, inquilino_id=inquilino_id, imovel_id=imovel_id,
        data_inicio=inicio, data_fim_prevista=fim, data_fim_real=fim_real,
        valor_mensal=valor, status=status, multa=multa,
    )


class RepoFake:
    def __init__(self, contratos=None, falhar_insercao=False):
        self.contratos = {c.id: c for c in (contratos or [])}
        self.falhar_insercao = falhar_insercao
        self.atrasados_marcados = 0

    def buscar_por_id(self, contrato_id):
        return self.contratos.get(contrato_id)

    def existe_aberto(self, imovel_id):
        return any(
            c.imovel_id == imovel_id and c.status != "encerrado"
            for c in self.contratos.values()
        )

    def listar(self, inquilino_id=None, status=None):
        return list(self.contratos.values())

    def inserir(self, inquilino_id, imovel_id, inicio, fim, valor_mensal):
        if self.falhar_insercao:
            raise RegraDeNegocio("índice parcial barrou: já existe aberto")
        novo = contrato(id=77, imovel_id=imovel_id, inquilino_id=inquilino_id,
                        inicio=inicio, fim=fim, valor=valor_mensal)
        self.contratos[77] = novo
        return 77

    def encerrar(self, contrato_id, fim_real, multa):
        atual = self.contratos[contrato_id]
        self.contratos[contrato_id] = atual.model_copy(
            update={"data_fim_real": fim_real, "status": "encerrado", "multa": multa}
        )

    def marcar_atrasados(self):
        self.atrasados_marcados += 1


class ImovelClientFake:
    def __init__(self, imovel=None, falhar_ao_liberar=False):
        self.imovel = imovel if imovel is not None else {
            "id": 5, "titulo": "Cobertura na Pajucara", "valor_mensal": 5200.0,
            "disponivel": True,
        }
        self.chamadas = []

    def buscar_imovel(self, imovel_id):
        if self.imovel is None or self.imovel["id"] != imovel_id:
            return None
        return self.imovel

    def definir_disponibilidade(self, imovel_id, disponivel):
        self.chamadas.append((imovel_id, disponivel))


# --------------------------------------------------------------- somar_meses

def test_somar_meses_ajusta_mes_curto():
    """31/01 + 1 mês não existe; cai no último dia de fevereiro."""
    assert somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_somar_meses_respeita_ano_bissexto():
    assert somar_meses(date(2028, 1, 31), 1) == date(2028, 2, 29)


def test_somar_meses_atravessa_o_ano():
    assert somar_meses(date(2026, 3, 15), 12) == date(2027, 3, 15)


# -------------------------------------------------------------- calcular_multa

def test_sem_atraso_nao_ha_multa():
    service = ContratoService(RepoFake(), ImovelClientFake())
    assert service.calcular_multa(contrato(), date(2026, 1, 10)) == 0.0


def test_saida_antes_do_prazo_nao_gera_multa():
    service = ContratoService(RepoFake(), ImovelClientFake())
    assert service.calcular_multa(contrato(), date(2025, 12, 1)) == 0.0


def test_multa_e_um_trinta_avos_do_aluguel_por_dia():
    """Aluguel de 3000, 10 dias de atraso: 3000/30 = 100/dia -> 1000."""
    service = ContratoService(RepoFake(), ImovelClientFake())
    assert service.calcular_multa(contrato(valor=3000.0), date(2026, 1, 20)) == 1000.0


def test_multa_acompanha_o_valor_do_contrato():
    """O mesmo atraso custa mais num imóvel mais caro.

    É exatamente o que a multa fixa de R$ 0,50 do acervo não expressava.
    """
    service = ContratoService(RepoFake(), ImovelClientFake())
    barato = service.calcular_multa(contrato(valor=900.0), date(2026, 1, 20))
    caro = service.calcular_multa(contrato(valor=5400.0), date(2026, 1, 20))
    assert caro > barato
    assert caro / barato == pytest.approx(6.0)


# ------------------------------------------------------------ registrar_contrato

def test_contrato_novo_dura_doze_meses():
    repo, cliente = RepoFake(), ImovelClientFake()
    service = ContratoService(repo, cliente)
    novo = service.registrar_contrato(ContratoCreate(inquilino_id=1, imovel_id=5))

    inicio = date.fromisoformat(novo.data_inicio)
    fim = date.fromisoformat(novo.data_fim_prevista)
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    assert meses == ContratoService.PRAZO_MESES == 12


def test_prazo_pode_ser_informado():
    service = ContratoService(RepoFake(), ImovelClientFake())
    novo = service.registrar_contrato(
        ContratoCreate(inquilino_id=1, imovel_id=5, meses=6)
    )
    inicio = date.fromisoformat(novo.data_inicio)
    fim = date.fromisoformat(novo.data_fim_prevista)
    assert (fim.year - inicio.year) * 12 + (fim.month - inicio.month) == 6


def test_contrato_grava_o_aluguel_acordado():
    """O aluguel do imóvel pode mudar depois; a multa é sobre o contratado."""
    cliente = ImovelClientFake()
    service = ContratoService(RepoFake(), cliente)
    novo = service.registrar_contrato(ContratoCreate(inquilino_id=1, imovel_id=5))
    assert novo.valor_mensal == cliente.imovel["valor_mensal"]


def test_registrar_ocupa_o_imovel():
    cliente = ImovelClientFake()
    service = ContratoService(RepoFake(), cliente)
    service.registrar_contrato(ContratoCreate(inquilino_id=1, imovel_id=5))
    assert cliente.chamadas == [(5, False)]


def test_imovel_inexistente_e_recusado():
    cliente = ImovelClientFake()
    cliente.imovel = None
    service = ContratoService(RepoFake(), cliente)
    with pytest.raises(RegraDeNegocio) as erro:
        service.registrar_contrato(ContratoCreate(inquilino_id=1, imovel_id=5))
    assert "não encontrado" in str(erro.value)


def test_um_contrato_aberto_por_imovel():
    """A regra que substituiu o 'usuário já tem este livro'.

    Vale para QUALQUER inquilino: o imóvel é único.
    """
    repo = RepoFake([contrato(id=1, imovel_id=5, inquilino_id=1)])
    service = ContratoService(repo, ImovelClientFake())
    with pytest.raises(RegraDeNegocio) as erro:
        service.registrar_contrato(ContratoCreate(inquilino_id=2, imovel_id=5))
    assert "já possui contrato em aberto" in str(erro.value)


def test_imovel_e_liberado_quando_a_insercao_falha():
    """Compensação: marcar o imóvel e falhar o INSERT deixaria imóvel preso.

    Cobre a corrida em que duas requisições passam pela checagem e o índice
    parcial do banco barra a segunda.
    """
    repo = RepoFake(falhar_insercao=True)
    cliente = ImovelClientFake()
    service = ContratoService(repo, cliente)

    with pytest.raises(RegraDeNegocio):
        service.registrar_contrato(ContratoCreate(inquilino_id=1, imovel_id=5))

    assert cliente.chamadas == [(5, False), (5, True)], (
        "o imóvel ficou ocupado sem contrato nenhum"
    )


# ------------------------------------------------------------- encerrar_contrato

def test_encerrar_libera_o_imovel():
    repo = RepoFake([contrato(id=1, imovel_id=5)])
    cliente = ImovelClientFake()
    service = ContratoService(repo, cliente)
    encerrado = service.encerrar_contrato(1)

    assert encerrado.status == "encerrado"
    assert cliente.chamadas == [(5, True)]


def test_encerrar_contrato_ja_encerrado_e_recusado():
    repo = RepoFake([contrato(id=1, status="encerrado")])
    service = ContratoService(repo, ImovelClientFake())
    with pytest.raises(RegraDeNegocio):
        service.encerrar_contrato(1)


def test_encerrar_contrato_inexistente():
    service = ContratoService(RepoFake(), ImovelClientFake())
    with pytest.raises(ContratoNaoEncontrado):
        service.encerrar_contrato(404)


def test_listar_marca_atrasados_antes_de_devolver():
    """Quem lista vê o status já atualizado, sem job separado."""
    repo = RepoFake([contrato()])
    service = ContratoService(repo, ImovelClientFake())
    service.listar_contratos()
    assert repo.atrasados_marcados == 1
