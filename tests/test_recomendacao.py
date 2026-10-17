"""Serviço de recomendação: pontuação por tipo e cidade, e as penalidades."""
import pytest

from conftest import carregar

servico_mod = carregar("recomendacao", "service")
RecomendacaoService = servico_mod.RecomendacaoService


def imovel(id=1, tipo="apartamento", cidade="Maceio", disponivel=True,
           valor=1500.0, titulo=None):
    return {
        "id": id, "titulo": titulo or f"Imóvel {id}", "tipo": tipo,
        "cidade": cidade, "disponivel": disponivel, "valor_mensal": valor,
    }


def contrato(imovel_id=1, status="ativo"):
    return {"imovel_id": imovel_id, "status": status}


class ContratoClientFake:
    def __init__(self, historico):
        self.historico = historico

    def buscar_historico(self, inquilino_id):
        return self.historico


class ImovelClientFake:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.chamadas = 0

    def buscar_portfolio_completo(self):
        self.chamadas += 1
        return self.portfolio


class RepoFake:
    def __init__(self, ja_recomendados=()):
        self.ja_recomendados = set(ja_recomendados)
        self.registrados = []

    def listar_recomendados(self, usuario_id):
        return self.ja_recomendados

    def registrar_recomendacoes(self, usuario_id, ids):
        self.registrados.extend(ids)


def montar(portfolio, historico, ja_recomendados=()):
    repo = RepoFake(ja_recomendados)
    service = RecomendacaoService(
        repo, ContratoClientFake(historico), ImovelClientFake(portfolio)
    )
    return repo, service


def test_perfil_sem_historico_vem_vazio():
    _, service = montar([], [])
    perfil = service.obter_perfil(1)
    assert perfil.total_contratos == 0
    assert perfil.tipos_favoritos == []
    assert perfil.cidades_favoritas == []


def test_perfil_sai_do_historico_de_contratos():
    portfolio = [imovel(id=1, tipo="casa", cidade="Recife")]
    _, service = montar(portfolio, [contrato(1), contrato(1)])
    perfil = service.obter_perfil(1)
    assert perfil.tipos_favoritos == ["casa"]
    assert perfil.cidades_favoritas == ["Recife"]
    assert perfil.total_contratos == 2


def test_tipo_e_cidade_preferidos_somam_pontos():
    """3 pontos pelo tipo + 2 pela cidade = 5, o máximo."""
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Recife")
    _, service = montar([alugado, candidato], [contrato(1)])
    recs = service.recomendar(1)
    assert len(recs) == 1
    assert recs[0].score == 5.0


def test_so_o_tipo_bate_rende_menos():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Maceio")
    _, service = montar([alugado, candidato], [contrato(1)])
    assert service.recomendar(1)[0].score == 3.0


def test_imovel_indisponivel_nao_e_recomendado():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Recife", disponivel=False)
    _, service = montar([alugado, candidato], [contrato(1)])
    assert service.recomendar(1) == []


def test_imovel_que_o_inquilino_ja_aluga_e_excluido():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    _, service = montar([alugado], [contrato(1)])
    assert service.recomendar(1) == []


def test_ja_recomendado_e_rebaixado_mas_nao_sumido():
    """A penalidade era 5, igual ao score máximo, e zerava a lista na segunda
    chamada. Com 55 livros passava; com ~9 imóveis disponíveis, não."""
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Recife")
    _, service = montar([alugado, candidato], [contrato(1)], ja_recomendados={2})

    recs = service.recomendar(1)
    assert len(recs) == 1, "o imóvel sumiu por já ter sido recomendado uma vez"
    assert recs[0].score == 4.0


def test_recomendacao_traz_o_aluguel():
    """Recomendar imóvel sem dizer o preço não serve para nada."""
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Recife", valor=4200.0)
    _, service = montar([alugado, candidato], [contrato(1)])
    assert service.recomendar(1)[0].valor_mensal == 4200.0


def test_resultado_vem_ordenado_por_score():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    so_tipo = imovel(id=2, tipo="casa", cidade="Maceio")
    tipo_e_cidade = imovel(id=3, tipo="casa", cidade="Recife")
    _, service = montar([alugado, so_tipo, tipo_e_cidade], [contrato(1)])
    recs = service.recomendar(1)
    assert [r.score for r in recs] == [5.0, 3.0]


def test_limite_corta_a_lista():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidatos = [imovel(id=i, tipo="casa", cidade="Recife") for i in range(2, 8)]
    _, service = montar([alugado] + candidatos, [contrato(1)])
    assert len(service.recomendar(1, limite=3)) == 3


def test_o_que_foi_recomendado_fica_registrado():
    alugado = imovel(id=1, tipo="casa", cidade="Recife")
    candidato = imovel(id=2, tipo="casa", cidade="Recife")
    repo, service = montar([alugado, candidato], [contrato(1)])
    service.recomendar(1)
    assert repo.registrados == [2]


def test_imovel_onde_ja_morou_volta_rebaixado():
    """A penalidade era 10, o dobro do score máximo: quem já tinha morado num
    imóvel nunca mais o via recomendado, mesmo com o contrato encerrado."""
    antigo = imovel(id=1, tipo="casa", cidade="Recife")
    novo = imovel(id=2, tipo="casa", cidade="Recife")
    _, service = montar([antigo, novo], [contrato(1, status="encerrado")])

    recs = service.recomendar(1)
    assert [r.imovel_id for r in recs] == [2, 1]
    assert "já morou" in recs[1].motivo


def test_historico_nao_custa_uma_chamada_por_contrato():
    portfolio = [imovel(id=i, tipo="casa", cidade="Recife") for i in range(1, 8)]
    historico = [contrato(i, status="encerrado") for i in range(1, 7)]
    cliente = ImovelClientFake(portfolio)
    service = RecomendacaoService(RepoFake(), ContratoClientFake(historico), cliente)

    service.recomendar(1)
    assert cliente.chamadas == 1
    service.obter_perfil(1)
    assert cliente.chamadas == 2
