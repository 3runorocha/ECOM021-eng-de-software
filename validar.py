#!/usr/bin/env python
"""Valida o que ja foi entregue. Rodar ao fim de cada semana, antes de comecar
o bloco seguinte.

    python validar.py             # tudo (sobe os servicos e derruba no fim)
    python validar.py --estatico  # so o que nao precisa subir servico

Cada checagem e uma funcao que levanta AssertionError com a explicacao quando
falha. As checagens vivas usam bancos temporarios, entao nao sujam os dados de
desenvolvimento. No bloco 15 isto virara uma suite pytest de verdade; por
enquanto e um script sem dependencia nova.
"""
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent
BIB = RAIZ / "biblioteca"
SERVICOS = ["catalogo", "usuarios", "emprestimos", "notificacoes", "recomendacao"]
PORTAS = (8000, 8001, 8002, 8003, 8004, 8005)
GATEWAY = "http://localhost:8000"

sys.path.insert(0, str(RAIZ))
import subir_servicos as launcher  # noqa: E402  (reusa a lista de servicos)


# ---------------------------------------------------------------- utilidades

def _fontes_py():
    for caminho in BIB.rglob("*.py"):
        if "__pycache__" in caminho.parts:
            continue
        yield caminho, caminho.read_text(encoding="utf-8")


def _porta_livre(porta):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", porta)) != 0


def _main_py(servico):
    return (BIB / "services" / servico / "main.py").read_text(encoding="utf-8")


# ------------------------------------------------------- bloco 1 (estatico)

def framework_exige_os_dois_hotspots():
    """1.1 - o contrato de hotspot obrigatorio precisa valer de novo."""
    sys.path.insert(0, str(BIB / "framework"))
    import framework

    abstratos = set(framework.FrameworkBiblioteca.__abstractmethods__)
    esperado = {"configurar_componentes", "executar_logica"}
    assert abstratos == esperado, (
        "__abstractmethods__ == {0}, esperado {1}. Provavelmente alguem "
        "redefiniu um hotspot abstrato como metodo concreto."
        .format(sorted(abstratos), sorted(esperado))
    )

    class Incompleta(framework.FrameworkBiblioteca):
        def executar_logica(self, contexto):
            return "ok"

    try:
        Incompleta()
    except TypeError:
        return
    raise AssertionError(
        "subclasse sem configurar_componentes foi instanciada; deveria ser barrada"
    )


def nenhuma_url_hardcoded():
    """1.5 - toda URL de servico tem de vir de env var."""
    problemas = []
    for caminho, texto in _fontes_py():
        for n, linha in enumerate(texto.splitlines(), 1):
            if "localhost" in linha and "getenv" not in linha:
                problemas.append("{0}:{1}: {2}".format(
                    caminho.relative_to(RAIZ), n, linha.strip()))

    api_js = RAIZ / "biblioteca-online" / "src" / "services" / "api.js"
    for n, linha in enumerate(api_js.read_text(encoding="utf-8").splitlines(), 1):
        if "localhost" in linha and "import.meta.env" not in linha:
            problemas.append("api.js:{0}: {1}".format(n, linha.strip()))

    assert not problemas, "URL fora de env var:\n  " + "\n  ".join(problemas)


def env_var_sobrescreve_url():
    """1.5 - nao basta existir getenv; a variavel tem de ter efeito."""
    codigo = (
        "import sys; sys.path[:0] = ['gateway', 'framework']\n"
        "import config, componentes\n"
        "print(config.SERVICES['catalogo']['url'])\n"
        "print(componentes.ComponenteCatalogoHTTP()._url)\n"
    )
    ambiente = dict(os.environ)
    ambiente["CATALOGO_URL"] = "http://maquina-b:9001"
    saida = subprocess.run(
        [sys.executable, "-c", codigo], cwd=BIB, env=ambiente,
        capture_output=True, text=True, timeout=60,
    )
    assert saida.returncode == 0, "falhou ao importar: " + saida.stderr
    linhas = saida.stdout.split()
    assert linhas == ["http://maquina-b:9001"] * 2, (
        "CATALOGO_URL nao foi respeitada; obtive {0}".format(linhas)
    )


def bancos_por_env_var():
    """DB_PATH externalizado - e o que permite validar sem sujar os dados."""
    faltando = []
    for servico in SERVICOS:
        linha = re.search(r"DB_PATH = .*", _main_py(servico))
        if linha is None or "os.getenv" not in linha.group(0):
            faltando.append(servico)
    assert not faltando, "DB_PATH ainda hardcoded em: " + ", ".join(faltando)


# ------------------------------------------------------- bloco 2 (estatico)

def sem_api_depreciada():
    """1.2 - on_event saiu, lifespan entrou nos 5 servicos."""
    for servico in SERVICOS:
        texto = _main_py(servico)
        assert "on_event" not in texto, servico + ": ainda usa @app.on_event"
        assert "lifespan=lifespan" in texto, (
            servico + ": lifespan nao registrado no FastAPI()")
        assert "@asynccontextmanager" in texto, (
            servico + ": lifespan nao e context manager")


def proxy_filtra_headers():
    """1.4 - os headers que descrevem o corpo nao podem ser repassados."""
    sys.path.insert(0, str(BIB / "gateway"))
    import proxy

    ignorados = proxy.ProxyService.HEADERS_NAO_REPASSADOS
    for header in ("content-encoding", "content-length",
                   "transfer-encoding", "connection"):
        assert header in ignorados, "proxy repassaria '{0}'".format(header)


def tudo_compila():
    saida = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(BIB),
         str(RAIZ / "validar.py"), str(RAIZ / "subir_servicos.py")],
        capture_output=True, text=True, timeout=180,
    )
    assert saida.returncode == 0, "erro de sintaxe:\n" + saida.stdout + saida.stderr


# ------------------------------------------------------------ checagens vivas

def health_geral(ctx):
    r = httpx.get(GATEWAY + "/health", timeout=10.0)
    assert r.status_code == 200, "/health devolveu {0}".format(r.status_code)
    corpo = r.json()
    assert corpo["status_geral"] == "ok", (
        "status_geral={0}: {1}".format(corpo["status_geral"], corpo))
    fora = [n for n, s in corpo["servicos"].items() if s["status"] != "ok"]
    assert not fora, "servicos fora do ar: {0}".format(fora)


def fluxo_completo_pelo_gateway(ctx):
    """Registro -> login -> cadastro -> leitura, tudo atravessando o proxy."""
    c = httpx.Client(base_url=GATEWAY, timeout=10.0)

    r = c.post("/usuarios/usuarios/registro", json={
        "nome": "Validador", "email": "validador@teste.br",
        "senha": "senha123", "tipo": "admin",
    })
    assert r.status_code == 201, "registro: {0} {1}".format(r.status_code, r.text)

    r = c.post("/usuarios/usuarios/login",
               json={"email": "validador@teste.br", "senha": "senha123"})
    assert r.status_code == 200, "login: {0} {1}".format(r.status_code, r.text)
    token = r.json().get("token")
    assert token, "login nao devolveu token: " + r.text
    ctx["token"] = token

    auth = {"Authorization": token}
    r = c.post("/catalogo/livros/", headers=auth, json={
        "titulo": "Item de validacao", "autor": "Script",
        "isbn": "000-validacao", "ano_publicacao": 2026,
        "genero": "teste", "quantidade_total": 3,
    })
    assert r.status_code == 201, "cadastro: {0} {1}".format(r.status_code, r.text)

    r = c.get("/catalogo/livros/", headers=auth)
    assert r.status_code == 200, "listagem: {0} {1}".format(r.status_code, r.text)
    titulos = [livro["titulo"] for livro in r.json()]
    assert "Item de validacao" in titulos, (
        "item cadastrado nao apareceu: {0}".format(titulos))


def resposta_comprimida_chega_intacta(ctx):
    """1.4 - o caso que o filtro de headers conserta."""
    r = httpx.get(GATEWAY + "/catalogo/livros/", timeout=10.0, headers={
        "Authorization": ctx["token"],
        "Accept-Encoding": "gzip, deflate",
    })
    assert r.status_code == 200, "{0} {1}".format(r.status_code, r.text)
    assert r.json(), "corpo vazio ou ilegivel"
    presentes = set(k.lower() for k in r.headers)
    assert "content-encoding" not in presentes, (
        "content-encoding do upstream foi repassado; o corpo ja vem descomprimido"
    )


def rota_protegida_exige_token(ctx):
    r = httpx.get(GATEWAY + "/catalogo/livros/", timeout=10.0)
    assert r.status_code == 401, (
        "sem token deveria dar 401, deu {0}".format(r.status_code))
    r = httpx.get(GATEWAY + "/catalogo/livros/", timeout=10.0,
                  headers={"Authorization": "token-falso"})
    assert r.status_code == 401, (
        "token invalido deveria dar 401, deu {0}".format(r.status_code))


ESTATICAS = [
    ("1", "framework exige os dois hotspots", framework_exige_os_dois_hotspots),
    ("1", "nenhuma URL hardcoded", nenhuma_url_hardcoded),
    ("1", "env var sobrescreve a URL", env_var_sobrescreve_url),
    ("1", "bancos vem de env var", bancos_por_env_var),
    ("2", "sem API depreciada (lifespan)", sem_api_depreciada),
    ("2", "proxy filtra headers do corpo", proxy_filtra_headers),
    ("-", "todo .py compila", tudo_compila),
]

VIVAS = [
    ("2", "health geral com os 6 no ar", health_geral),
    ("2", "fluxo completo pelo gateway", fluxo_completo_pelo_gateway),
    ("2", "resposta comprimida intacta", resposta_comprimida_chega_intacta),
    ("2", "rota protegida exige token", rota_protegida_exige_token),
]


# ------------------------------------------------------------------ execucao

def rodar(checagens, contexto=None):
    falhas = []
    for bloco, nome, funcao in checagens:
        try:
            if contexto is None:
                funcao()
            else:
                funcao(contexto)
            print("  [ok]    bloco {0}  {1}".format(bloco, nome))
        except Exception as erro:
            print("  [FALHA] bloco {0}  {1}".format(bloco, nome))
            for linha in str(erro).splitlines():
                print("          " + linha)
            falhas.append(nome)
    return falhas


def subir_para_teste(pasta_bancos):
    ambiente = dict(os.environ)
    for servico in SERVICOS:
        ambiente[servico.upper() + "_DB"] = str(pasta_bancos / (servico + ".db"))

    caminho_log = pasta_bancos / "servicos.log"
    log = open(caminho_log, "w", encoding="utf-8")
    processos = []
    for nome, pasta, porta in launcher.SERVICOS:
        processo = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", str(porta)],
            cwd=pasta, env=ambiente, stdout=log, stderr=subprocess.STDOUT,
        )
        processos.append((nome, porta, processo))
    return processos, log, caminho_log


def esperar_gateway(processos, limite=60):
    for _ in range(limite):
        for nome, porta, processo in processos:
            if processo.poll() is not None:
                return "'{0}' (:{1}) morreu ao subir, codigo {2}".format(
                    nome, porta, processo.returncode)
        try:
            if httpx.get(GATEWAY + "/health", timeout=2.0).status_code == 200:
                return None
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return "gateway nao respondeu a tempo"


def relatorio(falhas, vivas_puladas=False):
    print()
    if falhas:
        print("FALHOU: {0} checagem(ns) -> {1}".format(len(falhas), ", ".join(falhas)))
        return 1
    if vivas_puladas:
        print("Checagens estaticas passaram (as vivas foram puladas).")
        return 0
    print("Tudo passou. Pode seguir para o proximo bloco.")
    return 0


def main():
    print("\n=== Checagens estaticas ===")
    falhas = rodar(ESTATICAS)

    if "--estatico" in sys.argv:
        return relatorio(falhas, vivas_puladas=True)

    ocupadas = [p for p in PORTAS if not _porta_livre(p)]
    if ocupadas:
        print("\n[!] portas em uso: {0}. Pare os servicos e rode de novo.".format(ocupadas))
        return relatorio(falhas, vivas_puladas=True)

    pasta = Path(tempfile.mkdtemp(prefix="validacao-"))
    print("\n=== Checagens vivas (bancos temporarios) ===")
    processos, log, caminho_log = subir_para_teste(pasta)
    try:
        erro = esperar_gateway(processos)
        if erro:
            print("  [FALHA] nao subiu: " + erro)
            log.flush()
            print("  --- ultimas linhas do log ---")
            linhas = caminho_log.read_text(encoding="utf-8").splitlines()
            for linha in linhas[-15:]:
                print("          " + linha)
            falhas.append("subida dos servicos")
        else:
            falhas += rodar(VIVAS, contexto={})
    finally:
        launcher.encerrar(processos)
        log.close()
        restantes = [p for p in PORTAS if not _porta_livre(p)]
        if restantes:
            print("  [FALHA] portas nao liberadas no shutdown: {0}".format(restantes))
            falhas.append("shutdown limpo")
        else:
            print("  [ok]    bloco 2  shutdown liberou as 6 portas")
        shutil.rmtree(pasta, ignore_errors=True)

    return relatorio(falhas)


if __name__ == "__main__":
    sys.exit(main())
