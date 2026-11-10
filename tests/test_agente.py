"""Agente: a trava de dono nas ferramentas, a escolha do provedor e a leitura
da resposta do Gemini.

O agente chama o serviço de contratos por dentro, sem passar pelo gateway; sem
a trava, perguntar ao agente seria o atalho para ler contratos de outro
inquilino. Nenhum teste aqui chama uma API de modelo: as respostas do Gemini
são montadas com os tipos do próprio SDK.
"""
import json

import pytest
from google.genai import errors, types

from conftest import carregar

ferramentas, provedores, agente_mod, excecoes = carregar(
    "agente", "ferramentas", "provedores", "agente", "exceptions"
)
Agente = agente_mod.Agente
ProvedorGemini = provedores.ProvedorGemini
ProvedorAnthropic = provedores.ProvedorAnthropic
AgenteIndisponivel = excecoes.AgenteIndisponivel

ANA = {"id": 1, "tipo": "inquilino"}


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


@pytest.fixture
def sem_chaves(monkeypatch):
    for nome in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY",
                 "ANTHROPIC_AUTH_TOKEN", "AGENTE_PROVEDOR"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setattr(ProvedorAnthropic, "disponivel", lambda self: False)


def chamar_como(chamador, inquilino_id):
    marca = ferramentas.chamador_atual.set(chamador)
    try:
        return json.loads(ferramentas.listar_contratos(inquilino_id))
    finally:
        ferramentas.chamador_atual.reset(marca)


def test_inquilino_ve_os_proprios_contratos_pelo_agente(contratos):
    resultado = chamar_como(ANA, 1)
    assert contratos.pedidos == [1]
    assert resultado[0]["inquilino_id"] == 1


def test_agente_nao_mostra_contratos_de_outro_inquilino(contratos):
    resultado = chamar_como(ANA, 2)
    assert "erro" in resultado
    assert contratos.pedidos == [], "a ferramenta chegou a consultar o outro inquilino"


def test_admin_consulta_qualquer_inquilino_pelo_agente(contratos):
    chamar_como({"id": 9, "tipo": "admin"}, 2)
    assert contratos.pedidos == [2]


def test_sem_identidade_a_ferramenta_nao_e_restrita(contratos):
    """Uso interno (por uma app do framework), sem passar pelo gateway."""
    chamar_como(None, 2)
    assert contratos.pedidos == [2]


class ProvedorQueChamaFerramenta:
    """Faz o que o SDK faz: executa a ferramenta na mesma thread da pergunta."""

    nome, modelo = "falso", "modelo-falso"

    def __init__(self, inquilino_pedido):
        self.inquilino_pedido = inquilino_pedido
        self.resultado = None

    def disponivel(self):
        return True

    def responder(self, instrucoes, texto, lista):
        self.resultado = json.loads(dict((f.__name__, f) for f in lista)["listar_contratos"](self.inquilino_pedido))
        return {"resposta": "ok", "ferramentas_usadas": [], "truncado": False}


def test_trava_de_dono_vale_para_qualquer_provedor(contratos):
    provedor = ProvedorQueChamaFerramenta(inquilino_pedido=2)
    Agente(provedor).perguntar("meus contratos", chamador=ANA)
    assert "erro" in provedor.resultado
    assert contratos.pedidos == []


def test_sem_chave_nenhuma_o_agente_explica_o_que_configurar(sem_chaves):
    agente = Agente()
    assert agente.provedor == "gemini"
    assert agente.tem_credencial() is False
    with pytest.raises(AgenteIndisponivel) as erro:
        agente.perguntar("casa em Maceió")
    assert "GEMINI_API_KEY" in str(erro.value)
    assert "ANTHROPIC_API_KEY" in str(erro.value)


def test_chave_do_gemini_escolhe_o_gemini(sem_chaves, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    agente = Agente()
    assert (agente.provedor, agente.modelo) == ("gemini", "gemini-3.8-flash")
    assert agente.tem_credencial() is True


def test_agente_provedor_forca_a_escolha(sem_chaves, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.setenv("AGENTE_PROVEDOR", "anthropic")
    assert Agente().provedor == "anthropic"


def test_provedor_desconhecido_e_recusado(sem_chaves, monkeypatch):
    monkeypatch.setenv("AGENTE_PROVEDOR", "outro")
    with pytest.raises(ValueError):
        Agente()


class ModelosFake:
    """Devolve as respostas na ordem; uma exceção na lista é lançada."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def generate_content(self, model, contents, config):
        self.pedidos.append({"model": model, "contents": contents, "config": config})
        proxima = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        if isinstance(proxima, Exception):
            raise proxima
        return proxima


class ClienteFake:
    def __init__(self, *respostas):
        self.models = ModelosFake(*respostas)


def gemini_com(*respostas, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    monkeypatch.delenv("AGENTE_RESERVAS_GEMINI", raising=False)
    provedor = ProvedorGemini()
    provedor._cliente = ClienteFake(*respostas)
    return provedor


def sobrecarga():
    return errors.ServerError(503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}})


def resposta_do_gemini(texto, chamadas=()):
    historico = [types.Content(role="user", parts=[types.Part(text="pergunta")])]
    for nome, argumentos in chamadas:
        historico.append(types.Content(role="model", parts=[
            types.Part(function_call=types.FunctionCall(name=nome, args=argumentos))]))
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=texto)]))],
        automatic_function_calling_history=historico,
    )


def test_gemini_devolve_texto_e_ferramentas_usadas(monkeypatch):
    resposta = resposta_do_gemini("Achei a Casa no Tabuleiro, R$ 1.900.",
                                  [("buscar_imoveis", {"cidade": "Maceio", "tipo": "casa"})])
    provedor = gemini_com(resposta, monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")

    assert resultado["resposta"] == "Achei a Casa no Tabuleiro, R$ 1.900."
    assert resultado["ferramentas_usadas"] == [
        {"ferramenta": "buscar_imoveis", "argumentos": {"cidade": "Maceio", "tipo": "casa"}}]
    assert resultado["modelo"] == "gemini-3.8-flash"
    assert resultado["truncado"] is False


def test_gemini_recebe_as_tres_ferramentas_e_o_limite_de_chamadas(monkeypatch):
    provedor = gemini_com(resposta_do_gemini("ok"), monkeypatch=monkeypatch)
    Agente(provedor).perguntar("oi")
    config = provedor._cliente.models.pedidos[0]["config"]
    assert [f.__name__ for f in config.tools] == ["buscar_imoveis", "detalhar_imovel", "listar_contratos"]
    assert config.automatic_function_calling.maximum_remote_calls == provedores.MAX_ITERACOES


def test_gemini_redige_aviso_sem_ferramentas(monkeypatch):
    provedor = gemini_com(resposta_do_gemini("Seu contrato vence em 2 dias."), monkeypatch=monkeypatch)
    texto = Agente(provedor).redigir_aviso({"imovel": "Casa no Farol", "dias_restantes": 2})
    assert texto == "Seu contrato vence em 2 dias."
    assert not provedor._cliente.models.pedidos[0]["config"].tools


def test_gemini_aviso_vazio_vira_indisponivel(monkeypatch):
    provedor = gemini_com(resposta_do_gemini(""), monkeypatch=monkeypatch)
    with pytest.raises(AgenteIndisponivel):
        Agente(provedor).redigir_aviso({"imovel": "Casa no Farol"})


def test_modelo_sobrecarregado_passa_para_o_de_reserva(monkeypatch):
    provedor = gemini_com(sobrecarga(), resposta_do_gemini("Achei duas casas."), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")

    pedidos = provedor._cliente.models.pedidos
    assert [p["model"] for p in pedidos] == ["gemini-3.8-flash", "gemini-3.6-flash"]
    assert pedidos[1]["config"].thinking_config is None
    assert resultado["modelo"] == "gemini-3.6-flash"
    assert resultado["resposta"] == "Achei duas casas."


def test_todos_sobrecarregados_explica_o_erro(monkeypatch):
    provedor = gemini_com(sobrecarga(), monkeypatch=monkeypatch)
    with pytest.raises(AgenteIndisponivel, match="503"):
        Agente(provedor).perguntar("casa em Maceió")
    assert len(provedor._cliente.models.pedidos) == 3


def test_erro_que_nao_passa_nao_tenta_outro_modelo(monkeypatch):
    chave_invalida = errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}})
    provedor = gemini_com(chave_invalida, monkeypatch=monkeypatch)
    with pytest.raises(AgenteIndisponivel, match="API key not valid"):
        Agente(provedor).perguntar("casa em Maceió")
    assert len(provedor._cliente.models.pedidos) == 1
