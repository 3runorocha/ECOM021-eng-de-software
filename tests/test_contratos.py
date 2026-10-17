"""Serviço de contratos: prazo, multa, regra de um contrato por imóvel e a
compensação quando o INSERT falha depois de ocupar o imóvel."""
from datetime import date

import pytest

from conftest import carregar

modelos, servico_mod, excecoes = carregar(
    "contratos", "models", "service", "exceptions"
)

Contrato = modelos.Contrato
Chamador = modelos.Chamador
ContratoCreate = modelos.ContratoCreate
ContratoService = servico_mod.ContratoService
somar_meses = servico_mod.somar_meses
ContratoNaoEncontrado = excecoes.ContratoNaoEncontrado
PermissaoNegada = excecoes.PermissaoNegada
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
    def __init__(self, contratos=None, falhar_insercao=False, falhar_encerramento=False):
        self.contratos = {c.id: c for c in (contratos or [])}
        self.falhar_insercao = falhar_insercao
        self.falhar_encerramento = falhar_encerramento
        self.atrasados_marcados = 0
        self.hoje_recebido = None

    def buscar_por_id(self, contrato_id):
        return self.contratos.get(contrato_id)

    def existe_aberto(self, imovel_id):
        return any(
            c.imovel_id == imovel_id and c.status != "encerrado"
            for c in self.contratos.values()
        )

    def listar(self, inquilino_id=None, status=None):
        return [
            c for c in self.contratos.values()
            if inquilino_id is None or c.inquilino_id == inquilino_id
        ]

    def inserir(self, inquilino_id, imovel_id, inicio, fim, valor_mensal):
        if self.falhar_insercao:
            raise RegraDeNegocio("índice parcial barrou: já existe aberto")
        novo = contrato(id=77, imovel_id=imovel_id, inquilino_id=inquilino_id,
                        inicio=inicio, fim=fim, valor=valor_mensal)
        self.contratos[77] = novo
        return 77

    def encerrar(self, contrato_id, fim_real, multa):
        if self.falhar_encerramento:
            raise RuntimeError("disco cheio")
        atual = self.contratos[contrato_id]
        self.contratos[contrato_id] = atual.model_copy(
            update={"data_fim_real": fim_real, "status": "encerrado", "multa": multa}
        )

    def marcar_atrasados(self, hoje):
        self.atrasados_marcados += 1
        self.hoje_recebido = hoje


class ImovelClientFake:
    def __init__(self, imovel=None, ja_livre=False):
        self.imovel = imovel if imovel is not None else {
            "id": 5, "titulo": "Cobertura na Pajucara", "valor_mensal": 5200.0,
            "disponivel": True,
        }
        self.chamadas = []
        self.ja_livre = ja_livre

    def buscar_imovel(self, imovel_id):
        if self.imovel is None or self.imovel["id"] != imovel_id:
            return None
        return self.imovel

    def definir_disponibilidade(self, imovel_id, disponivel):
        self.chamadas.append((imovel_id, disponivel))
        if disponivel and self.ja_livre:
            raise RegraDeNegocio("Imóvel já está disponível")


def test_somar_meses_ajusta_mes_curto():
    """31/01 + 1 mês não existe; cai no último dia de fevereiro."""
    assert somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_somar_meses_respeita_ano_bissexto():
    assert somar_meses(date(2028, 1, 31), 1) == date(2028, 2, 29)


def test_somar_meses_atravessa_o_ano():
    assert somar_meses(date(2026, 3, 15), 12) == date(2027, 3, 15)


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


def test_encerrar_libera_o_imovel():
    repo = RepoFake([contrato(id=1, imovel_id=5)])
    cliente = ImovelClientFake()
    service = ContratoService(repo, cliente)
    encerrado = service.encerrar_contrato(1)

    assert encerrado.status == "encerrado"
    assert cliente.chamadas == [(5, True)]


def test_encerrar_com_imovel_ja_livre_ainda_encerra():
    """Um admin liberou o imóvel à mão antes; o contrato não pode ficar preso."""
    repo = RepoFake([contrato(id=1, imovel_id=5)])
    service = ContratoService(repo, ImovelClientFake(ja_livre=True))
    assert service.encerrar_contrato(1).status == "encerrado"


def test_encerrar_que_falha_ao_gravar_reocupa_o_imovel():
    repo = RepoFake([contrato(id=1, imovel_id=5)], falhar_encerramento=True)
    cliente = ImovelClientFake()
    service = ContratoService(repo, cliente)
    with pytest.raises(RuntimeError):
        service.encerrar_contrato(1)

    assert cliente.chamadas == [(5, True), (5, False)], (
        "o imóvel ficou livre com o contrato ainda ativo"
    )
    assert repo.contratos[1].status == "ativo"


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


def test_atraso_usa_a_mesma_data_que_a_multa():
    """O SQL comparava com date('now') do SQLite, que é UTC, enquanto a multa
    usa date.today(), local. Em UTC-3, entre 21h e meia-noite, o contrato
    aparecia atrasado com multa zero. Agora a data vem do Python."""
    repo = RepoFake([contrato()])
    ContratoService(repo, ImovelClientFake()).listar_contratos()
    assert repo.hoje_recebido == str(date.today())


ANA = Chamador(id=1, tipo="inquilino")
BIA = Chamador(id=2, tipo="inquilino")
ADMIN = Chamador(id=9, tipo="admin")


def _dois_inquilinos():
    return RepoFake([
        contrato(id=1, imovel_id=5, inquilino_id=1),
        contrato(id=2, imovel_id=6, inquilino_id=2),
    ])


def test_inquilino_so_ve_os_proprios_contratos():
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    assert [c.id for c in service.listar_contratos(chamador=ANA)] == [1]


def test_inquilino_nao_lista_contratos_de_outro():
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    with pytest.raises(PermissaoNegada):
        service.listar_contratos(inquilino_id=2, chamador=ANA)


def test_contrato_de_outro_inquilino_parece_inexistente():
    """404 em vez de 403: não revela que o contrato existe."""
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    with pytest.raises(ContratoNaoEncontrado):
        service.buscar_contrato(2, chamador=ANA)


def test_inquilino_nao_encerra_contrato_de_outro():
    cliente = ImovelClientFake()
    service = ContratoService(_dois_inquilinos(), cliente)
    with pytest.raises(ContratoNaoEncontrado):
        service.encerrar_contrato(2, chamador=ANA)
    assert cliente.chamadas == [], "o imóvel do outro não pode ter sido liberado"


def test_inquilino_encerra_o_proprio_contrato():
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    assert service.encerrar_contrato(1, chamador=ANA).status == "encerrado"


def test_inquilino_nao_assina_em_nome_de_outro():
    service = ContratoService(RepoFake(), ImovelClientFake())
    with pytest.raises(PermissaoNegada):
        service.registrar_contrato(
            ContratoCreate(inquilino_id=2, imovel_id=5), chamador=ANA
        )


def test_inquilino_assina_o_proprio_contrato():
    service = ContratoService(RepoFake(), ImovelClientFake())
    novo = service.registrar_contrato(
        ContratoCreate(inquilino_id=1, imovel_id=5), chamador=ANA
    )
    assert novo.inquilino_id == 1


def test_admin_ve_e_mexe_em_tudo():
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    assert {c.id for c in service.listar_contratos(chamador=ADMIN)} == {1, 2}
    assert service.buscar_contrato(2, chamador=ADMIN).inquilino_id == 2
    assert service.encerrar_contrato(2, chamador=ADMIN).status == "encerrado"


def test_chamada_interna_sem_identidade_nao_e_restrita():
    """Notificações e recomendação chamam contratos direto, sem passar pelo
    gateway; sem identidade, a chamada é de outro serviço e vê tudo."""
    service = ContratoService(_dois_inquilinos(), ImovelClientFake())
    assert {c.id for c in service.listar_contratos()} == {1, 2}
