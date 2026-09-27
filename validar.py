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

from datetime import date

import httpx

RAIZ = Path(__file__).resolve().parent
BIB = RAIZ / "biblioteca"
SERVICOS = ["imoveis", "usuarios", "contratos", "notificacoes", "recomendacao"]
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
        "print(config.SERVICES['imoveis']['url'])\n"
        "print(componentes.ComponenteImovelHTTP()._url)\n"
    )
    ambiente = dict(os.environ)
    ambiente["IMOVEIS_URL"] = "http://maquina-b:9001"
    saida = subprocess.run(
        [sys.executable, "-c", codigo], cwd=BIB, env=ambiente,
        capture_output=True, text=True, timeout=60,
    )
    assert saida.returncode == 0, "falhou ao importar: " + saida.stderr
    linhas = saida.stdout.split()
    assert linhas == ["http://maquina-b:9001"] * 2, (
        "IMOVEIS_URL nao foi respeitada; obtive {0}".format(linhas)
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
    ctx["auth"] = auth
    r = c.post("/imoveis/imoveis/", headers=auth, json={
        "titulo": "Imovel de validacao", "tipo": "apartamento",
        "endereco": "Rua de Teste, 1", "cidade": "Maceio",
        "quartos": 2, "banheiros": 1, "area_m2": 60.0, "valor_mensal": 1800.0,
    })
    assert r.status_code == 201, "cadastro: {0} {1}".format(r.status_code, r.text)
    criado = r.json()
    assert criado["disponivel"] is True, "imovel novo deveria nascer disponivel"
    ctx["imovel_id"] = criado["id"]

    r = c.get("/imoveis/imoveis/", headers=auth)
    assert r.status_code == 200, "listagem: {0} {1}".format(r.status_code, r.text)
    titulos = [imovel["titulo"] for imovel in r.json()]
    assert "Imovel de validacao" in titulos, (
        "item cadastrado nao apareceu: {0}".format(titulos))


def resposta_comprimida_chega_intacta(ctx):
    """1.4 - o caso que o filtro de headers conserta."""
    r = httpx.get(GATEWAY + "/imoveis/imoveis/", timeout=10.0, headers={
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
    r = httpx.get(GATEWAY + "/imoveis/imoveis/", timeout=10.0)
    assert r.status_code == 401, (
        "sem token deveria dar 401, deu {0}".format(r.status_code))
    r = httpx.get(GATEWAY + "/imoveis/imoveis/", timeout=10.0,
                  headers={"Authorization": "token-falso"})
    assert r.status_code == 401, (
        "token invalido deveria dar 401, deu {0}".format(r.status_code))


def modelo_imovel_substituiu_o_livro():
    """2.2 - o modelo novo nao pode carregar campo de acervo de biblioteca."""
    modelo = (BIB / "services" / "imoveis" / "models.py").read_text(encoding="utf-8")
    for campo in ("tipo", "cidade", "valor_mensal", "disponivel", "quartos"):
        assert campo in modelo, "Imovel sem o campo {0}".format(campo)
    for herdado in ("isbn", "genero", "autor", "quantidade_total"):
        assert herdado not in modelo, (
            "models.py ainda tem {0}, campo do acervo de livros".format(herdado))


def componente_imovel_e_booleano():
    """2.3/2.6 - o contrato do componente acompanhou a mudanca de semantica."""
    sys.path.insert(0, str(BIB / "framework"))
    import interfaces

    metodos = set(interfaces.IComponenteImovel.__abstractmethods__)
    for metodo in ("buscar_imoveis", "cadastrar_imovel", "definir_disponibilidade"):
        assert metodo in metodos, (
            "IComponenteImovel sem {0}; tem {1}".format(metodo, sorted(metodos)))
    assert not hasattr(interfaces, "IComponenteCatalogo"), (
        "IComponenteCatalogo ainda existe")


def filtros_de_imovel(ctx):
    """2.4 - os filtros novos precisam filtrar de verdade."""
    auth = ctx["auth"]
    base = GATEWAY + "/imoveis/imoveis/"

    r = httpx.get(base, headers=auth, params={"cidade": "Maceio"}, timeout=10.0)
    assert r.status_code == 200, r.text
    assert all(i["cidade"] == "Maceio" for i in r.json()), "filtro de cidade vazou"

    r = httpx.get(base, headers=auth, params={"tipo": "casa"}, timeout=10.0)
    assert r.status_code == 200, r.text
    assert all(i["tipo"] == "casa" for i in r.json()), "filtro de tipo vazou"

    r = httpx.get(base, headers=auth, params={"quartos_min": 2}, timeout=10.0)
    assert all(i["quartos"] >= 2 for i in r.json()), "filtro de quartos vazou"

    r = httpx.get(base, headers=auth, params={"valor_max": 2000}, timeout=10.0)
    assert all(i["valor_mensal"] <= 2000 for i in r.json()), "filtro de valor vazou"

    r = httpx.get(base, headers=auth,
                  params={"valor_min": 5000, "valor_max": 100}, timeout=10.0)
    assert r.status_code == 400, (
        "faixa de valor invertida deveria dar 400, deu {0}".format(r.status_code))


def disponibilidade_e_booleana(ctx):
    """2.3 - substituiu o delta inteiro e mantem a guarda de estado."""
    url = "{0}/imoveis/imoveis/{1}/disponibilidade".format(GATEWAY, ctx["imovel_id"])
    auth = ctx["auth"]

    r = httpx.patch(url, headers=auth, params={"disponivel": False}, timeout=10.0)
    assert r.status_code == 200, "alugar: {0} {1}".format(r.status_code, r.text)
    assert r.json()["disponivel"] is False, r.text

    r = httpx.patch(url, headers=auth, params={"disponivel": False}, timeout=10.0)
    assert r.status_code == 400, (
        "alugar imovel ja alugado deveria dar 400, deu {0}".format(r.status_code))

    r = httpx.patch(url, headers=auth, params={"disponivel": True}, timeout=10.0)
    assert r.status_code == 200, "liberar: {0} {1}".format(r.status_code, r.text)


def modelo_contrato_substituiu_o_emprestimo():
    """3.1-3.3 - entidade, campos e datas renomeados."""
    modelo = (BIB / "services" / "contratos" / "models.py").read_text(encoding="utf-8")
    for campo in ("inquilino_id", "imovel_id", "data_inicio",
                  "data_fim_prevista", "valor_mensal"):
        assert campo in modelo, "Contrato sem o campo {0}".format(campo)
    for herdado in ("usuario_id", "livro_id", "data_emprestimo", "data_devolucao"):
        assert herdado not in modelo, (
            "models.py ainda tem {0}, campo de emprestimo".format(herdado))


def prazo_em_meses_e_multa_proporcional():
    """3.4-3.5 - prazo de 12 meses e multa de 1/30 do aluguel por dia."""
    fonte = (BIB / "services" / "contratos" / "service.py").read_text(encoding="utf-8")
    assert "PRAZO_MESES = 12" in fonte, "PRAZO_MESES nao e 12"
    # Procura a atribuicao, nao o nome: o comentario do service.py cita
    # MULTA_POR_DIA justamente para explicar que ele foi substituido.
    assert not re.search(r"^\s*MULTA_POR_DIA\s*=", fonte, re.M), (
        "MULTA_POR_DIA fixo voltou; a multa deve sair do valor_mensal")

    partes = [
        "from datetime import date",
        "from models import Contrato",
        "from service import ContratoService, somar_meses",
        "print(somar_meses(date(2026, 1, 31), 1))",
        "print(somar_meses(date(2026, 3, 15), 12))",
        "c = Contrato(id=1, inquilino_id=1, imovel_id=1,"
        " data_inicio='2025-01-10', data_fim_prevista='2026-01-10',"
        " data_fim_real=None, valor_mensal=3000.0, status='ativo', multa=0.0)",
        "s = ContratoService(None, None)",
        "print(s.calcular_multa(c, date(2026, 1, 10)))",
        "print(s.calcular_multa(c, date(2026, 1, 20)))",
    ]
    codigo = chr(10).join(partes)

    saida = subprocess.run(
        [sys.executable, "-c", codigo], cwd=str(BIB / "services" / "contratos"),
        capture_output=True, text=True, timeout=60,
    )
    assert saida.returncode == 0, "falhou ao calcular: " + saida.stderr
    linhas = saida.stdout.split()

    # 31/01 + 1 mes cai em 28/02 (2026 nao e bissexto), nao em 31/02.
    assert linhas[0] == "2026-02-28", "somar_meses errou mes curto: " + linhas[0]
    assert linhas[1] == "2027-03-15", "somar_meses errou 12 meses: " + linhas[1]
    assert linhas[2] == "0.0", "sem atraso deveria dar multa 0, deu " + linhas[2]
    # 10 dias de atraso sobre aluguel de 3000: 3000/30 = 100/dia -> 1000.
    assert linhas[3] == "1000.0", (
        "10 dias de atraso sobre R$3000 deveria dar 1000.0, deu " + linhas[3])


def ciclo_de_contrato(ctx):
    """3.6-3.8 - registrar, ocupar o imovel, encerrar, liberar."""
    c = httpx.Client(base_url=GATEWAY, timeout=10.0)
    auth = ctx["auth"]
    imovel_id = ctx["imovel_id"]

    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 1, "imovel_id": imovel_id})
    assert r.status_code == 201, "registrar: {0} {1}".format(r.status_code, r.text)
    contrato = r.json()
    ctx["contrato_id"] = contrato["id"]
    assert contrato["status"] == "ativo", contrato
    assert contrato["valor_mensal"] == 1800.0, (
        "contrato deveria gravar o aluguel do imovel: {0}".format(contrato))

    # 12 meses depois da assinatura
    inicio = date.fromisoformat(contrato["data_inicio"])
    fim = date.fromisoformat(contrato["data_fim_prevista"])
    meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month)
    assert meses == 12, "prazo deveria ser 12 meses, deu {0}".format(meses)

    r = c.get("/imoveis/imoveis/{0}".format(imovel_id), headers=auth)
    assert r.json()["disponivel"] is False, "assinar contrato deveria ocupar o imovel"

    r = c.post("/contratos/contratos/{0}/encerrar".format(ctx["contrato_id"]),
               headers=auth)
    assert r.status_code == 200, "encerrar: {0} {1}".format(r.status_code, r.text)
    encerrado = r.json()
    assert encerrado["status"] == "encerrado", encerrado
    assert encerrado["multa"] == 0.0, "encerrar no prazo nao deveria ter multa"

    r = c.get("/imoveis/imoveis/{0}".format(imovel_id), headers=auth)
    assert r.json()["disponivel"] is True, "encerrar deveria liberar o imovel"


def um_contrato_aberto_por_imovel(ctx):
    """3.7 - a regra que substitui o 'usuario ja tem este livro'."""
    c = httpx.Client(base_url=GATEWAY, timeout=10.0)
    auth = ctx["auth"]
    imovel_id = ctx["imovel_id"]

    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 2, "imovel_id": imovel_id})
    assert r.status_code == 201, "primeiro contrato: {0} {1}".format(r.status_code, r.text)
    primeiro = r.json()["id"]

    # Outro inquilino, mesmo imovel: tem de ser barrado.
    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 3, "imovel_id": imovel_id})
    assert r.status_code == 400, (
        "segundo contrato no mesmo imovel deveria dar 400, deu {0} {1}"
        .format(r.status_code, r.text))

    # E o imovel nao pode ter ficado solto pela compensacao.
    r = c.get("/imoveis/imoveis/{0}".format(imovel_id), headers=auth)
    assert r.json()["disponivel"] is False, (
        "o imovel do contrato em vigor nao pode voltar a disponivel")

    c.post("/contratos/contratos/{0}/encerrar".format(primeiro), headers=auth)


ESTATICAS = [
    ("1", "framework exige os dois hotspots", framework_exige_os_dois_hotspots),
    ("1", "nenhuma URL hardcoded", nenhuma_url_hardcoded),
    ("1", "env var sobrescreve a URL", env_var_sobrescreve_url),
    ("1", "bancos vem de env var", bancos_por_env_var),
    ("2", "sem API depreciada (lifespan)", sem_api_depreciada),
    ("2", "proxy filtra headers do corpo", proxy_filtra_headers),
    ("3", "modelo Imovel substituiu o Livro", modelo_imovel_substituiu_o_livro),
    ("4", "componente usa disponibilidade booleana", componente_imovel_e_booleano),
    ("6", "modelo Contrato substituiu o Emprestimo", modelo_contrato_substituiu_o_emprestimo),
    ("7", "prazo em meses e multa proporcional", prazo_em_meses_e_multa_proporcional),
    ("-", "todo .py compila", tudo_compila),
]

VIVAS = [
    ("2", "health geral com os 6 no ar", health_geral),
    ("2", "fluxo completo pelo gateway", fluxo_completo_pelo_gateway),
    ("2", "resposta comprimida intacta", resposta_comprimida_chega_intacta),
    ("2", "rota protegida exige token", rota_protegida_exige_token),
    ("4", "filtros de imovel filtram", filtros_de_imovel),
    ("4", "disponibilidade e booleana", disponibilidade_e_booleana),
    ("8", "ciclo de contrato completo", ciclo_de_contrato),
    ("8", "um contrato aberto por imovel", um_contrato_aberto_por_imovel),
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
