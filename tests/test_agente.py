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

ferramentas, provedores, agente_mod, excecoes, contingencia = carregar(
    "agente", "ferramentas", "provedores", "agente", "exceptions", "contingencia"
)
Agente = agente_mod.Agente
ProvedorGemini = provedores.ProvedorGemini
ProvedorAnthropic = provedores.ProvedorAnthropic
AgenteIndisponivel = excecoes.AgenteIndisponivel
ModeloLento = excecoes.ModeloLento

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


@pytest.fixture(autouse=True)
def sem_pausas():
    """A pausa de modelo com problema e do processo; cada teste comeca limpo."""
    ProvedorGemini._pausados.clear()
    yield
    ProvedorGemini._pausados.clear()


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
    assert (agente.provedor, agente.modelo) == ("gemini", "gemini-3.5-flash-lite")
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
        self.pedidos.append({"model": model, "contents": list(contents) if isinstance(contents, list) else contents,
                             "config": config})
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
    monkeypatch.delenv("AGENTE_MODELO_GEMINI", raising=False)
    provedor = ProvedorGemini()
    provedor._cliente = ClienteFake(*respostas)
    return provedor


def sobrecarga():
    return errors.ServerError(503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}})


def texto(conteudo):
    return types.GenerateContentResponse(candidates=[
        types.Candidate(content=types.Content(role="model", parts=[types.Part(text=conteudo)]))])


def chamada(nome, argumentos):
    return types.GenerateContentResponse(candidates=[
        types.Candidate(content=types.Content(role="model", parts=[
            types.Part(function_call=types.FunctionCall(name=nome, args=argumentos))]))])


class ImoveisFake:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.filtros = []

    def buscar_imoveis(self, filtros):
        self.filtros.append(filtros)
        return [i for i in self.portfolio if i["cidade"] == filtros.get("cidade", i["cidade"])]


def imovel(id, titulo, cidade="Maceio"):
    return {"id": id, "titulo": titulo, "tipo": "casa", "cidade": cidade, "endereco": "Rua X, 1",
            "quartos": 3, "banheiros": 2, "area_m2": 110.0, "valor_mensal": 1900.0, "disponivel": True}


@pytest.fixture
def portfolio(monkeypatch):
    fake = ImoveisFake([imovel(1, "Casa no Tabuleiro"), imovel(2, "Casa no Bessa", "Joao Pessoa")])
    monkeypatch.setattr(ferramentas, "imoveis", fake)
    return fake


def test_gemini_chama_a_ferramenta_e_devolve_o_texto(monkeypatch, portfolio):
    provedor = gemini_com(chamada("buscar_imoveis", {"cidade": "Maceio", "quartos_min": 2.0}),
                          texto("Encontrei 1 casa: Casa no Tabuleiro."), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")

    assert resultado["resposta"] == "Encontrei 1 casa: Casa no Tabuleiro."
    assert resultado["ferramentas_usadas"][0]["ferramenta"] == "buscar_imoveis"
    assert [i["titulo"] for i in resultado["imoveis"]] == ["Casa no Tabuleiro"]
    assert resultado["modelo"] == "gemini-3.5-flash-lite"
    assert portfolio.filtros[0]["quartos_min"] == 2 and isinstance(portfolio.filtros[0]["quartos_min"], int), (
        "o 2.0 do Gemini tem de chegar ao serviço como inteiro")
    segunda = provedor._cliente.models.pedidos[1]["contents"]
    assert segunda[-1].parts[0].function_response.name == "buscar_imoveis"


def test_gemini_conduz_o_laco_e_recebe_as_tres_ferramentas(monkeypatch):
    provedor = gemini_com(texto("ok"), monkeypatch=monkeypatch)
    Agente(provedor).perguntar("oi")
    config = provedor._cliente.models.pedidos[0]["config"]
    assert [f.__name__ for f in config.tools] == ["buscar_imoveis", "detalhar_imovel", "listar_contratos"]
    assert config.automatic_function_calling.disable is True, (
        "com o SDK conduzindo o laço, cada ida ganhava prazo próprio")


def test_gemini_nao_repete_tentativas_por_conta_propria(monkeypatch):
    """Quem troca de modelo e o provedor; o SDK repetindo o mesmo modelo
    sobrecarregado deixava a pergunta em quase um minuto."""
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste")
    cliente = ProvedorGemini()._obter_cliente()
    assert cliente._api_client._http_options.retry_options.attempts == 1


def test_cada_chamada_tem_prazo_curto(monkeypatch):
    provedor = gemini_com(texto("ok"), monkeypatch=monkeypatch)
    Agente(provedor).perguntar("oi")
    opcoes = provedor._cliente.models.pedidos[0]["config"].http_options
    assert 0 < opcoes.timeout <= ProvedorGemini.PRAZO_CHAMADA * 1000
    assert opcoes.headers["X-Server-Timeout"] == "10", (
        "sem o cabecalho, o servidor recebe o prazo curto e recusa com 400")


def test_gemini_redige_aviso_sem_ferramentas(monkeypatch):
    provedor = gemini_com(texto("Seu contrato vence em 2 dias."), monkeypatch=monkeypatch)
    resultado = Agente(provedor).redigir_aviso({"imovel": "Casa no Farol", "dias_restantes": 2})
    assert resultado == "Seu contrato vence em 2 dias."
    assert not provedor._cliente.models.pedidos[0]["config"].tools


def test_gemini_aviso_vazio_vira_indisponivel(monkeypatch):
    provedor = gemini_com(texto(""), monkeypatch=monkeypatch)
    with pytest.raises(AgenteIndisponivel):
        Agente(provedor).redigir_aviso({"imovel": "Casa no Farol"})


def test_modelo_sobrecarregado_passa_para_o_de_reserva(monkeypatch):
    provedor = gemini_com(sobrecarga(), texto("Achei duas casas."), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")

    pedidos = provedor._cliente.models.pedidos
    assert [p["model"] for p in pedidos] == ["gemini-3.5-flash-lite", "gemini-3.6-flash"]
    assert pedidos[0]["config"].thinking_config is None, "o lite nao aceita nivel de raciocinio"
    assert pedidos[1]["config"].thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert resultado["modelo"] == "gemini-3.6-flash"


def test_depois_da_ferramenta_continua_no_mesmo_modelo(monkeypatch, portfolio):
    provedor = gemini_com(sobrecarga(), chamada("buscar_imoveis", {"cidade": "Maceio"}), texto("ok"),
                          monkeypatch=monkeypatch)
    Agente(provedor).perguntar("casa em Maceió")
    modelos = [p["model"] for p in provedor._cliente.models.pedidos]
    assert modelos == ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.6-flash"]


def test_tempo_esgotado_depois_da_busca_resume_pelos_imoveis(monkeypatch, portfolio):
    provedor = gemini_com(chamada("buscar_imoveis", {"cidade": "Maceio"}), sobrecarga(), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")

    assert resultado["resposta"].startswith("Encontrei 1 imóvel")
    assert [i["titulo"] for i in resultado["imoveis"]] == ["Casa no Tabuleiro"]
    assert resultado["truncado"] is True


def test_busca_sem_resultado_e_sem_texto_explica(monkeypatch, portfolio):
    provedor = gemini_com(chamada("buscar_imoveis", {"cidade": "Recife"}), sobrecarga(), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Recife")
    assert resultado["resposta"].startswith("Não encontrei imóveis")
    assert resultado["imoveis"] == []


def test_todos_sobrecarregados_caem_na_busca_direta(monkeypatch, portfolio):
    provedor = gemini_com(sobrecarga(), monkeypatch=monkeypatch)
    resultado = Agente(provedor).perguntar("casa em Maceió")
    assert len(provedor._cliente.models.pedidos) == 3
    assert resultado["modelo"] == "busca direta (contingência)"
    assert [i["titulo"] for i in resultado["imoveis"]] == ["Casa no Tabuleiro"]


def test_erro_que_nao_passa_nao_tenta_outro_modelo(monkeypatch):
    chave_invalida = errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}})
    provedor = gemini_com(chave_invalida, monkeypatch=monkeypatch)
    with pytest.raises(AgenteIndisponivel, match="API key not valid"):
        Agente(provedor).perguntar("casa em Maceió")
    assert len(provedor._cliente.models.pedidos) == 1


def test_modelo_com_problema_fica_de_fora_na_pergunta_seguinte(monkeypatch):
    provedor = gemini_com(sobrecarga(), texto("ok"), monkeypatch=monkeypatch)
    agente = Agente(provedor)
    agente.perguntar("primeira")
    agente.perguntar("segunda")
    modelos = [p["model"] for p in provedor._cliente.models.pedidos]
    assert modelos == ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.6-flash"], (
        "a segunda pergunta voltou a esperar o modelo sobrecarregado")


class ProvedorQueBusca:
    nome, modelo = "falso", "modelo-falso"

    def disponivel(self):
        return True

    def responder(self, instrucoes, texto_pergunta, lista):
        ferramenta = dict((f.__name__, f) for f in lista)
        ferramenta["buscar_imoveis"](cidade="Maceio")
        ferramenta["detalhar_imovel"](1)
        return {"resposta": "Achei duas casas.", "ferramentas_usadas": [], "truncado": False}


def test_resposta_traz_os_imoveis_encontrados_para_os_cartoes(monkeypatch):
    portfolio_maceio = [imovel(1, "Casa no Tabuleiro"), imovel(2, "Casa no Farol"),
                        imovel(3, "Casa no Bessa", "Joao Pessoa")]
    monkeypatch.setattr(ferramentas, "imoveis", ImoveisFake(portfolio_maceio))
    resultado = Agente(ProvedorQueBusca()).perguntar("casa em Maceió")

    assert [i["titulo"] for i in resultado["imoveis"]] == ["Casa no Tabuleiro", "Casa no Farol"], (
        "o imovel detalhado de novo nao pode aparecer duas vezes")
    assert "disponivel" not in resultado["imoveis"][0]
    assert ferramentas.imoveis_encontrados.get() is None, "a lista vazou para fora da pergunta"


def test_instrucoes_pedem_texto_simples_e_curto():
    assert "sem Markdown" in agente_mod.INSTRUCOES
    assert "no máximo três frases" in agente_mod.INSTRUCOES


def test_depois_da_busca_a_chamada_usa_o_tempo_que_resta(monkeypatch, portfolio):
    """Sem outro modelo para tentar, o prazo curto so cortava o resumo do modelo."""
    provedor = gemini_com(chamada("buscar_imoveis", {"cidade": "Maceio"}), texto("ok"), monkeypatch=monkeypatch)
    Agente(provedor).perguntar("casa em Maceió")
    primeira, segunda = [p["config"].http_options.timeout for p in provedor._cliente.models.pedidos]
    assert primeira <= ProvedorGemini.PRAZO_CHAMADA * 1000
    assert segunda > ProvedorGemini.PRAZO_CHAMADA * 1000


@pytest.mark.parametrize("pergunta, esperado", [
    ("casa em Maceió até 3 mil", {"cidade": "Maceio", "tipo": "casa", "valor_max": 3000.0}),
    ("apartamento de 2 quartos em Recife", {"cidade": "Recife", "tipo": "apartamento", "quartos_min": 2}),
    ("tem kitnet?", {"tipo": "apartamento"}),
    ("até R$ 1.800 em joao pessoa", {"cidade": "Joao Pessoa", "valor_max": 1800.0}),
    ("me ajuda", {}),
])
def test_contingencia_tira_os_filtros_da_frase(pergunta, esperado):
    assert contingencia.extrair_filtros(pergunta) == esperado


class ProvedorLento:
    nome, modelo = "gemini", "gemini-3.5-flash-lite"

    def disponivel(self):
        return True

    def responder(self, instrucoes, texto_pergunta, lista):
        raise ModeloLento("O modelo não respondeu a tempo")


def test_modelo_lento_cai_na_busca_direta_e_avisa(monkeypatch, portfolio):
    resultado = Agente(ProvedorLento()).perguntar("casa em Maceió até 3 mil")

    assert resultado["resposta"].startswith("O modelo não respondeu a tempo, então fiz uma busca direta")
    assert [i["titulo"] for i in resultado["imoveis"]] == ["Casa no Tabuleiro"]
    assert resultado["modelo"] == "busca direta (contingência)"
    assert portfolio.filtros[0]["cidade"] == "Maceio"


def test_sem_credencial_nao_vira_contingencia(sem_chaves):
    with pytest.raises(AgenteIndisponivel) as erro:
        Agente().perguntar("casa em Maceió")
    assert not isinstance(erro.value, ModeloLento)
