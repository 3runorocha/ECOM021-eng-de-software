"""Ferramentas do agente: a de contratos respeita a regra de dono.

O agente chama o serviço de contratos por dentro, sem passar pelo gateway; sem
esta trava, perguntar ao agente seria o atalho para ler contratos de outro
inquilino. Nenhum teste aqui chama a API da Anthropic.
"""
import json

import pytest

from conftest import carregar

ferramentas = carregar("agente", "ferramentas")


class ContratosFake:
    def __init__(self):
        self.pedidos = []

    def listar_contratos(self, inquilino_id=None):
        self.pedidos.append(inquilino_id)
        return [{"id": 1, "inquilino_id": inquilino_id}]


@pytest.fixture
def contratos(monkeypatch):
    fake = ContratosFake()
    monkeypatch.setattr(ferramentas, "contratos", fake)
    return fake


def chamar_como(chamador, inquilino_id):
    marca = ferramentas.chamador_atual.set(chamador)
    try:
        return json.loads(ferramentas.listar_contratos.call({"inquilino_id": inquilino_id}))
    finally:
        ferramentas.chamador_atual.reset(marca)


def test_inquilino_ve_os_proprios_contratos_pelo_agente(contratos):
    resultado = chamar_como({"id": 1, "tipo": "inquilino"}, 1)
    assert contratos.pedidos == [1]
    assert resultado[0]["inquilino_id"] == 1


def test_agente_nao_mostra_contratos_de_outro_inquilino(contratos):
    resultado = chamar_como({"id": 1, "tipo": "inquilino"}, 2)
    assert "erro" in resultado
    assert contratos.pedidos == [], "a ferramenta chegou a consultar o outro inquilino"


def test_admin_consulta_qualquer_inquilino_pelo_agente(contratos):
    chamar_como({"id": 9, "tipo": "admin"}, 2)
    assert contratos.pedidos == [2]


def test_sem_identidade_a_ferramenta_nao_e_restrita(contratos):
    """Uso interno (por uma app do framework), sem passar pelo gateway."""
    chamar_como(None, 2)
    assert contratos.pedidos == [2]
