"""Teste de integração: o ciclo de locação inteiro passando pelo gateway.

Diferente dos demais, este exige os serviços no ar. Rode `python
subir_servicos.py` antes; sem isso os testes são pulados, não falham.

    python -m pytest tests/ -m integracao

Deixa dados no banco de desenvolvimento (um imóvel e um contrato encerrado),
como qualquer uso manual deixaria.
"""
import os
import uuid

import httpx
import pytest

GATEWAY = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")

pytestmark = pytest.mark.integracao


def servicos_no_ar():
    try:
        r = httpx.get(f"{GATEWAY}/health", timeout=3.0)
        return r.status_code == 200 and r.json().get("status_geral") == "ok"
    except httpx.RequestError:
        return False


@pytest.fixture(scope="module")
def cliente():
    if not servicos_no_ar():
        pytest.skip(f"serviços fora do ar em {GATEWAY} — rode subir_servicos.py")
    return httpx.Client(base_url=GATEWAY, timeout=30.0)


@pytest.fixture(scope="module")
def auth(cliente):
    """Cria um usuário próprio do teste, para não depender do seed."""
    email = f"teste-{uuid.uuid4().hex[:8]}@alugue.br"
    r = cliente.post("/usuarios/usuarios/registro", json={
        "nome": "Usuário de Teste", "email": email,
        "senha": "senha123", "tipo": "inquilino",
    })
    assert r.status_code == 201, r.text
    usuario_id = r.json()["id"]

    r = cliente.post("/usuarios/usuarios/login",
                     json={"email": email, "senha": "senha123"})
    assert r.status_code == 200, r.text
    return {"Authorization": r.json()["token"]}, usuario_id


def test_rota_protegida_exige_token(cliente):
    assert cliente.get("/imoveis/imoveis/").status_code == 401


def test_ciclo_de_locacao_ponta_a_ponta(cliente, auth):
    """Cadastrar imóvel, assinar, ver o imóvel ocupado, encerrar, ver liberado.

    Passa por três serviços (imóveis, usuários, contratos) e pelo gateway.
    """
    cabecalhos, inquilino_id = auth

    r = cliente.post("/imoveis/imoveis/", headers=cabecalhos, json={
        "titulo": f"Imóvel de teste {uuid.uuid4().hex[:6]}", "tipo": "apartamento",
        "endereco": "Rua da Integração, 1", "cidade": "Maceio",
        "quartos": 2, "banheiros": 1, "area_m2": 60.0, "valor_mensal": 1800.0,
    })
    assert r.status_code == 201, r.text
    imovel = r.json()
    assert imovel["disponivel"] is True

    r = cliente.post("/contratos/contratos/", headers=cabecalhos, json={
        "inquilino_id": inquilino_id, "imovel_id": imovel["id"],
    })
    assert r.status_code == 201, r.text
    contrato = r.json()
    assert contrato["status"] == "ativo"
    assert contrato["valor_mensal"] == imovel["valor_mensal"], (
        "o contrato deve gravar o aluguel acordado"
    )

    r = cliente.get(f"/imoveis/imoveis/{imovel['id']}", headers=cabecalhos)
    assert r.json()["disponivel"] is False, "assinar deveria ocupar o imóvel"

    # Segundo contrato no mesmo imóvel, por outro inquilino: barrado.
    r = cliente.post("/contratos/contratos/", headers=cabecalhos, json={
        "inquilino_id": inquilino_id + 1, "imovel_id": imovel["id"],
    })
    assert r.status_code == 400, (
        f"segundo contrato no mesmo imóvel deveria dar 400, deu {r.status_code}"
    )

    r = cliente.post(f"/contratos/contratos/{contrato['id']}/encerrar",
                     headers=cabecalhos)
    assert r.status_code == 200, r.text
    encerrado = r.json()
    assert encerrado["status"] == "encerrado"
    assert encerrado["multa"] == 0.0, "encerrar no prazo não gera multa"

    r = cliente.get(f"/imoveis/imoveis/{imovel['id']}", headers=cabecalhos)
    assert r.json()["disponivel"] is True, "encerrar deveria liberar o imóvel"


def test_filtros_de_imovel_filtram_no_servico(cliente, auth):
    cabecalhos, _ = auth
    r = cliente.get("/imoveis/imoveis/", headers=cabecalhos,
                    params={"cidade": "Maceio", "tipo": "apartamento"})
    assert r.status_code == 200, r.text
    for imovel in r.json():
        assert imovel["cidade"] == "Maceio"
        assert imovel["tipo"] == "apartamento"


def test_agente_responde_sobre_a_propria_disponibilidade(cliente, auth):
    """Não chama o modelo: só confere que o serviço está integrado ao gateway."""
    cabecalhos, _ = auth
    r = cliente.get("/agente/agente/status", headers=cabecalhos)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert "credencial_configurada" in corpo
    assert "buscar_imoveis" in corpo["ferramentas"]
