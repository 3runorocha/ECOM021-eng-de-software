"""O framework: Template Method, frozen spots e hotspots.

É o argumento de reúso do projeto (herdado do trabalho de RDS), então o que
estes testes protegem é o contrato: a ordem é do framework, os pontos de
adaptação são da aplicação, e nenhuma app reescreve o fluxo.
"""
import pytest

from conftest import carregar_framework

framework_mod = carregar_framework("framework")
FrameworkBiblioteca = framework_mod.FrameworkBiblioteca


class ComponenteEspiao:
    def __init__(self, registro, nome="espiao"):
        self.registro = registro
        self.nome = nome

    def inicializar(self):
        self.registro.append(f"inicializar:{self.nome}")

    def finalizar(self):
        self.registro.append(f"finalizar:{self.nome}")

    def get_nome(self):
        return self.nome


def app_de_teste(registro, logica=None, campos=None):
    class AppTeste(FrameworkBiblioteca):
        def configurar_componentes(self):
            self.registrar_componente("espiao", ComponenteEspiao(registro))

        def get_campos_obrigatorios(self):
            return campos or []

        def pre_processar(self, contexto):
            registro.append("pre_processar")

        def executar_logica(self, contexto):
            registro.append("executar_logica")
            if logica is not None:
                return logica(contexto)
            return {"ok": True}

        def pos_processar(self, contexto, resultado):
            registro.append("pos_processar")

        def tratar_erro(self, contexto, erro):
            registro.append("tratar_erro")
            return {"erro": True, "mensagem": str(erro)}

    return AppTeste()


# ------------------------------------------------------------------ contrato

def test_os_dois_hotspots_sao_obrigatorios():
    """Sem isto, uma app que esquece configurar_componentes roda com zero
    componentes e só quebra mais tarde, em get_componente."""
    assert FrameworkBiblioteca.__abstractmethods__ == {
        "configurar_componentes", "executar_logica"
    }


def test_subclasse_incompleta_nao_instancia():
    class Incompleta(FrameworkBiblioteca):
        def executar_logica(self, contexto):
            return "ok"

    with pytest.raises(TypeError):
        Incompleta()


def test_componente_nao_registrado_da_erro_util():
    registro = []
    app = app_de_teste(registro)
    app.configurar_componentes()
    with pytest.raises(KeyError) as erro:
        app.get_componente("inexistente")
    assert "configurar_componentes" in str(erro.value)


# -------------------------------------------------------------------- ordem

def test_ordem_do_template_method():
    registro = []
    app_de_teste(registro).executar_operacao({})
    assert registro == [
        "inicializar:espiao",
        "pre_processar",
        "executar_logica",
        "pos_processar",
        "finalizar:espiao",
    ]


def test_componentes_sao_finalizados_mesmo_com_erro():
    """Frozen spot: o encerramento não depende do que a app fez."""
    registro = []

    def explode(contexto):
        raise ValueError("falhou no meio")

    app_de_teste(registro, logica=explode).executar_operacao({})
    assert registro == [
        "inicializar:espiao",
        "pre_processar",
        "executar_logica",
        "tratar_erro",
        "finalizar:espiao",
    ]
    assert "pos_processar" not in registro


def test_erro_na_logica_vira_resultado_tratado():
    registro = []

    def explode(contexto):
        raise ValueError("falhou no meio")

    resultado = app_de_teste(registro, logica=explode).executar_operacao({})
    assert resultado["erro"] is True
    assert "falhou no meio" in resultado["mensagem"]


# ------------------------------------------------------------ pré-condições

def test_campo_obrigatorio_ausente_barra_antes_da_logica():
    registro = []
    app_de_teste(registro, campos=["imovel_id"]).executar_operacao({})
    assert "executar_logica" not in registro
    assert "tratar_erro" in registro


def test_campo_obrigatorio_presente_deixa_seguir():
    registro = []
    app_de_teste(registro, campos=["imovel_id"]).executar_operacao({"imovel_id": 5})
    assert "executar_logica" in registro


# ----------------------------------------------------------------------- log

def test_execucao_fica_registrada_no_log():
    app = app_de_teste([])
    app.executar_operacao({"imovel_id": 5})
    log = app.get_log()
    assert len(log) == 1
    assert log[0]["operacao"] == "AppTeste"
    assert log[0]["status"] == "ok"
    assert "duracao_segundos" in log[0]


def test_log_marca_falha():
    def explode(contexto):
        raise ValueError("falhou")

    app = app_de_teste([], logica=explode)
    app.executar_operacao({})
    assert app.get_log()[0]["status"] == "erro"


def test_log_nao_guarda_senha():
    """O contexto pode carregar credencial; o log não pode."""
    app = app_de_teste([])
    app.executar_operacao({"email": "a@b.c", "senha": "segredo123"})
    resumo = app.get_log()[0]["contexto_resumo"]
    assert "email" in resumo
    assert "senha" not in resumo


def test_duas_execucoes_acumulam_log():
    app = app_de_teste([])
    app.executar_operacao({})
    app.executar_operacao({})
    assert len(app.get_log()) == 2
