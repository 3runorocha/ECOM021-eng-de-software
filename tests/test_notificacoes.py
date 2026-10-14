"""Serviço de notificações: a varredura que gera alertas dos contratos."""
from datetime import date, timedelta

import pytest

from conftest import carregar

modelos, servico_mod = carregar("notificacoes", "models", "service")

NotificacaoService = servico_mod.NotificacaoService


def contrato_dict(status="atrasado", dias=-61, valor=5200.0, imovel_id=5,
                  inquilino_id=1):
    fim = date.today() + timedelta(days=dias)
    return {
        "id": 1, "inquilino_id": inquilino_id, "imovel_id": imovel_id,
        "data_inicio": "2025-01-01", "data_fim_prevista": fim.isoformat(),
        "data_fim_real": None, "valor_mensal": valor, "status": status,
        "multa": 0.0,
    }


class RepoFake:
    def __init__(self, ja_notificados=()):
        self.inseridos = []
        self.ja_notificados = set(ja_notificados)

    def inserir(self, dados):
        self.inseridos.append(dados)
        return len(self.inseridos)

    def existe_nao_lida(self, usuario_id, imovel_id, tipos):
        return (usuario_id, imovel_id) in self.ja_notificados


class ContratoClientFake:
    def __init__(self, contratos):
        self.contratos = contratos

    def listar_contratos(self):
        return self.contratos


def rodar(contratos, ja_notificados=()):
    repo = RepoFake(ja_notificados)
    service = NotificacaoService(repo, ContratoClientFake(contratos))
    resultado = service.executar_varredura()
    return repo, resultado


def test_contrato_vencido_gera_alerta_de_atraso():
    repo, _ = rodar([contrato_dict(status="atrasado", dias=-61)])
    assert len(repo.inseridos) == 1
    assert repo.inseridos[0].tipo == "atraso"


def test_multa_do_alerta_acompanha_o_aluguel():
    """5200/30 x 61 = 10573.33. A conta sai do contrato, não de constante fixa."""
    repo, _ = rodar([contrato_dict(valor=5200.0, dias=-61)])
    assert "10573.33" in repo.inseridos[0].mensagem


def test_alugueis_diferentes_geram_multas_diferentes():
    caro, _ = rodar([contrato_dict(valor=5400.0, dias=-61)])
    barato, _ = rodar([contrato_dict(valor=1700.0, dias=-61)])
    assert caro.inseridos[0].mensagem != barato.inseridos[0].mensagem


def test_contrato_perto_do_fim_gera_alerta_de_prazo():
    repo, _ = rodar([contrato_dict(status="ativo", dias=1)])
    assert repo.inseridos[0].tipo == "prazo_proximo"


def test_contrato_longe_do_fim_nao_gera_nada():
    repo, _ = rodar([contrato_dict(status="ativo", dias=200)])
    assert repo.inseridos == []


def test_contrato_encerrado_e_ignorado():
    repo, _ = rodar([contrato_dict(status="encerrado", dias=-61)])
    assert repo.inseridos == []


def test_nao_repete_alerta_ja_pendente():
    """Rodar a varredura duas vezes não enche a caixa do inquilino."""
    repo, _ = rodar([contrato_dict()], ja_notificados={(1, 5)})
    assert repo.inseridos == []


def test_alerta_aponta_o_imovel():
    repo, _ = rodar([contrato_dict(imovel_id=17)])
    assert repo.inseridos[0].imovel_id == 17


def test_varredura_conta_o_que_gerou():
    _, resultado = rodar([
        contrato_dict(imovel_id=5, inquilino_id=1),
        contrato_dict(imovel_id=11, inquilino_id=2),
    ])
    assert "2 notificação(ões)" in resultado["mensagem"]
