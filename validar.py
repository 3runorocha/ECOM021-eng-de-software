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
SERVICOS_TODOS = SERVICOS + ["agente"]
PORTAS = (8000, 8001, 8002, 8003, 8004, 8005, 8006)
GATEWAY = "http://127.0.0.1:8000"

sys.path.insert(0, str(RAIZ))
import subir_servicos as launcher


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


def sem_comentarios(texto, marcadores=("#", "//")):
    """Tira linhas de comentario antes de procurar codigo no fonte.

    Existe porque ja me enganei duas vezes: um comentario que explica a
    remocao de algo cita o proprio nome removido, e a checagem acusava
    regressao onde nao havia.
    """
    limpas = []
    for linha in texto.splitlines():
        nua = linha.strip()
        if any(nua.startswith(m) for m in marcadores):
            continue
        limpas.append(linha)
    return chr(10).join(limpas)


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
    """1.5 - toda URL de servico vem de env var, e nunca aponta para localhost.

    O host importa: no Windows, localhost resolve ::1 antes de 127.0.0.1 e o
    uvicorn escuta so em IPv4, entao cada chamada entre servicos espera ~2s
    antes de cair no IPv4. Medido: 2133 ms com localhost, 20 ms com 127.0.0.1.
    """
    problemas = []
    for caminho, texto in _fontes_py():
        for n, linha in enumerate(texto.splitlines(), 1):
            rotulo = "{0}:{1}: {2}".format(caminho.relative_to(RAIZ), n, linha.strip())
            if "http://127.0.0.1:" in linha and "getenv" not in linha:
                problemas.append("fora de env var -> " + rotulo)
            if "http://localhost:" in linha:
                problemas.append("usa localhost (lento no Windows) -> " + rotulo)

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


def sem_api_depreciada():
    """1.2 - on_event saiu, lifespan entrou em todos os servicos."""
    for servico in SERVICOS_TODOS:
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
    assert "MULTA_POR_DIA" not in sem_comentarios(fonte), (
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

    assert linhas[0] == "2026-02-28", "somar_meses errou mes curto: " + linhas[0]
    assert linhas[1] == "2027-03-15", "somar_meses errou 12 meses: " + linhas[1]
    assert linhas[2] == "0.0", "sem atraso deveria dar multa 0, deu " + linhas[2]
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

    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 3, "imovel_id": imovel_id})
    assert r.status_code == 400, (
        "segundo contrato no mesmo imovel deveria dar 400, deu {0} {1}"
        .format(r.status_code, r.text))

    r = c.get("/imoveis/imoveis/{0}".format(imovel_id), headers=auth)
    assert r.json()["disponivel"] is False, (
        "o imovel do contrato em vigor nao pode voltar a disponivel")

    c.post("/contratos/contratos/{0}/encerrar".format(primeiro), headers=auth)


def pagina_de_imoveis_substituiu_catalogo():
    """5.2 - a tela de catalogo saiu e a rota aponta para a nova."""
    paginas = RAIZ / "biblioteca-online" / "src" / "pages"
    assert (paginas / "Imoveis.jsx").exists(), "falta pages/Imoveis.jsx"
    assert not (paginas / "Catalogo.jsx").exists(), "pages/Catalogo.jsx ainda existe"

    app = (RAIZ / "biblioteca-online" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "/imoveis" in app, "App.jsx sem a rota /imoveis"
    assert "Catalogo" not in app, "App.jsx ainda importa Catalogo"


def frontend_nao_inventa_dados():
    """5.1 - a tela nao pode fingir que funciona quando o backend esta fora.

    A pagina antiga caia num array MOCK de livros no .catch, e o Sidebar tinha
    a lista de servicos fixa com ok: true -- tudo verde com os servicos
    derrubados. Os dois mascaravam falha de backend.
    """
    paginas = RAIZ / "biblioteca-online" / "src" / "pages"
    for arquivo in sorted(paginas.glob("*.jsx")):
        pagina = sem_comentarios(arquivo.read_text(encoding="utf-8"))
        assert "MOCK" not in pagina, (
            "{0} tem dados falsos de fallback".format(arquivo.name))
        if arquivo.name != "Login.jsx":
            assert "setErro" in pagina, (
                "{0} sem estado de erro: falha de backend fica invisivel"
                .format(arquivo.name))

    sidebar = sem_comentarios(
        (RAIZ / "biblioteca-online" / "src" / "components" / "Sidebar.jsx")
        .read_text(encoding="utf-8"))
    assert "ok: true" not in sidebar, (
        "Sidebar voltou a ter status de servico fixo em ok: true")
    assert "healthAPI" in sidebar, "Sidebar nao consulta o /health do gateway"


def frontend_compila():
    """5.x - o build do Vite tem de passar."""
    front = RAIZ / "biblioteca-online"
    if not (front / "node_modules").exists():
        raise AssertionError(
            "node_modules ausente; rode 'npm install' em biblioteca-online "
            "para esta checagem valer")

    npm = "npm.cmd" if os.name == "nt" else "npm"
    saida = subprocess.run(
        [npm, "run", "build"], cwd=str(front),
        capture_output=True, text=True, timeout=300,
    )
    assert saida.returncode == 0, (
        "build do frontend falhou:" + chr(10)
        + saida.stdout[-2000:] + saida.stderr[-2000:])


def pagina_de_contratos_substituiu_emprestimos():
    """5.3 - a tela de emprestimos saiu e a rota aponta para a nova."""
    paginas = RAIZ / "biblioteca-online" / "src" / "pages"
    assert (paginas / "Contratos.jsx").exists(), "falta pages/Contratos.jsx"
    assert not (paginas / "Emprestimos.jsx").exists(), "pages/Emprestimos.jsx ainda existe"

    app = (RAIZ / "biblioteca-online" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "/contratos" in app, "App.jsx sem a rota /contratos"
    assert "Emprestimos" not in app, "App.jsx ainda importa Emprestimos"

    pagina = sem_comentarios((paginas / "Contratos.jsx").read_text(encoding="utf-8"))
    assert "encerrado" in pagina, "a tela nao conhece o status encerrado"
    assert "devolvido" not in pagina, (
        "a tela ainda fala de status devolvido, que era do acervo de livros")


def tela_nao_duplica_a_regra_de_multa():
    """A multa e regra de negocio: vive no servico, nao na tela.

    A tela mostra os dias em atraso, que e apresentacao. Se ela passar a
    calcular dinheiro, a regra fica em dois lugares e eles divergem.
    """
    pagina = sem_comentarios(
        (RAIZ / "biblioteca-online" / "src" / "pages" / "Contratos.jsx")
        .read_text(encoding="utf-8"))
    for pista in ("valor_mensal /", "valor_mensal/", "valor_mensal *", "valor_mensal*"):
        assert pista not in pagina, (
            "Contratos.jsx faz conta com valor_mensal ({0}); a multa e do servico"
            .format(pista))


def configurador_foi_removido():
    """5.5 - era tela da LPS da disciplina antiga, fora de escopo aqui."""
    paginas = RAIZ / "biblioteca-online" / "src" / "pages"
    assert not (paginas / "Configurador.jsx").exists(), (
        "pages/Configurador.jsx ainda existe")
    for arquivo in ("App.jsx", "components/Sidebar.jsx"):
        texto = (RAIZ / "biblioteca-online" / "src" / arquivo).read_text(encoding="utf-8")
        assert "onfigurador" not in texto, (
            "{0} ainda referencia o Configurador".format(arquivo))


def frontend_sem_vocabulario_de_biblioteca():
    """5.x - nenhuma tela pode continuar falando do dominio antigo."""
    base = RAIZ / "biblioteca-online" / "src"
    problemas = []
    for arquivo in sorted(base.rglob("*.jsx")) + sorted(base.rglob("*.js")):
        texto = sem_comentarios(arquivo.read_text(encoding="utf-8"))
        for termo in ("livro", "Livro", "autor", "genero", "emprestimo", "Emprestimo"):
            if termo in texto:
                problemas.append("{0}: {1}".format(arquivo.name, termo))
    assert not problemas, "vocabulario do acervo de livros no frontend: " + ", ".join(problemas)


def recomendacao_responde_rapido(ctx):
    """O servico de recomendacao chama imoveis uma vez por contrato do
    historico. Com host errado isso custava 14s e estourava o gateway."""
    inicio = time.perf_counter()
    r = httpx.get(GATEWAY + "/recomendacao/recomendacao/perfil/1",
                  headers=ctx["auth"], timeout=20.0)
    duracao = time.perf_counter() - inicio
    assert r.status_code == 200, "perfil: {0} {1}".format(r.status_code, r.text)
    assert duracao < 5.0, (
        "perfil levou {0:.1f}s; chamada entre servicos esta lenta (host errado?)"
        .format(duracao))

    r = httpx.get(GATEWAY + "/recomendacao/recomendacao/1",
                  headers=ctx["auth"], timeout=20.0)
    assert r.status_code == 200, "recomendar: {0} {1}".format(r.status_code, r.text)


def agente_usa_a_camada_de_componentes():
    """4.1 - o argumento de arquitetura do projeto.

    O agente nao pode falar HTTP direto com os servicos: as ferramentas dele
    sao a mesma camada de componentes que as apps do framework usam. Se este
    check cair, o agente virou um cliente paralelo e o reuso deixou de valer.
    """
    fonte = (BIB / "services" / "agente" / "ferramentas.py").read_text(encoding="utf-8")
    assert "from componentes import" in fonte, (
        "ferramentas.py nao importa a camada de componentes do framework")
    for componente in ("ComponenteImovelHTTP", "ComponenteContratoHTTP"):
        assert componente in fonte, "ferramentas.py sem {0}".format(componente)
    assert "import httpx" not in sem_comentarios(fonte), (
        "ferramentas.py fala HTTP direto; deveria passar pelos componentes")


def ferramentas_do_agente_sao_de_leitura():
    """4.1 - o modelo nao executa acao com efeito colateral nesta fase."""
    fonte = sem_comentarios(
        (BIB / "services" / "agente" / "ferramentas.py").read_text(encoding="utf-8"))
    for escrita in ("registrar_contrato", "encerrar_contrato",
                    "definir_disponibilidade", "cadastrar_imovel"):
        assert escrita not in fonte, (
            "ferramenta de escrita exposta ao modelo: {0}".format(escrita))


def agente_usa_modelo_atual():
    """O id do modelo tem de ser um da geracao atual, nao um inventado."""
    fonte = (BIB / "services" / "agente" / "provedores.py").read_text(encoding="utf-8")
    assert "claude-opus-5-5" in fonte, (
        "o agente nao esta no modelo padrao claude-opus-5-5")
    assert "gemini-3.8-flash" in fonte, (
        "o provedor Gemini nao esta no modelo padrao gemini-3.8-flash")
    assert not re.search(r"claude-[a-z0-9.-]*-\d{8}", fonte), (
        "id de modelo com sufixo de data: esses nao existem")


def agente_degrada_sem_credencial(ctx):
    """4.1 - sem chave o servico sobe e explica; nao devolve 500.

    Quando HA credencial configurada, este check NAO faz a pergunta: rodar o
    validador nao pode gastar dinheiro na API a cada execucao.
    """
    r = httpx.get(GATEWAY + "/agente/agente/status", headers=ctx["auth"], timeout=15.0)
    assert r.status_code == 200, "status: {0} {1}".format(r.status_code, r.text)
    corpo = r.json()
    assert "credencial_configurada" in corpo, corpo
    assert len(corpo.get("ferramentas", [])) >= 3, corpo

    if corpo["credencial_configurada"]:
        return

    r = httpx.post(GATEWAY + "/agente/agente/perguntar", headers=ctx["auth"],
                   json={"texto": "apartamento 2 quartos em Maceio"}, timeout=30.0)
    assert r.status_code == 503, (
        "sem credencial deveria dar 503 com explicacao, deu {0} {1}"
        .format(r.status_code, r.text))
    for chave in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        assert chave in r.text, (
            "a mensagem de erro nao diz o que configurar ({0}): {1}".format(chave, r.text))


def agente_aceita_gemini_ou_claude():
    """Revisao (10/11): o agente roda com o Gemini (nivel gratuito) ou o Claude.

    As ferramentas nao podem depender de SDK nenhum, senao trocar de provedor
    obriga a reescrever a camada que fala com os componentes.
    """
    pasta = BIB / "services" / "agente"
    provedores = sem_comentarios((pasta / "provedores.py").read_text(encoding="utf-8"))
    for nome in ("class ProvedorGemini", "class ProvedorAnthropic", "def escolher_provedor",
                 "AGENTE_PROVEDOR", "GEMINI_API_KEY"):
        assert nome in provedores, "provedores.py sem {0}".format(nome)
    ferramentas = sem_comentarios((pasta / "ferramentas.py").read_text(encoding="utf-8"))
    for sdk in ("anthropic", "google.genai", "from google"):
        assert sdk not in ferramentas, "ferramentas.py depende de SDK: {0}".format(sdk)
    rotas = (pasta / "routes.py").read_text(encoding="utf-8")
    assert '"provedor"' in rotas and '"modelo"' in rotas, (
        "/agente/status nao diz qual provedor e modelo estao em uso")
    lancador = (RAIZ / "subir_servicos.py").read_text(encoding="utf-8")
    assert "def ler_env" in lancador, "subir_servicos.py nao le o .env da raiz"
    assert "class ModeloLento" in (pasta / "exceptions.py").read_text(encoding="utf-8"), (
        "falta distinguir modelo lento de falta de credencial")
    contingencia = sem_comentarios((pasta / "contingencia.py").read_text(encoding="utf-8"))
    assert "def extrair_filtros" in contingencia, "falta a busca de contingencia"
    assert "ORCAMENTO" in provedores and "PRAZO_CHAMADA" in provedores, (
        "o provedor do Gemini nao tem orcamento de tempo por pergunta")
    gateway = (BIB / "gateway" / "config.py").read_text(encoding="utf-8")
    linha_agente = next(l for l in gateway.splitlines() if '"agente"' in l)
    assert '"timeout"' in linha_agente, (
        "o gateway espera o agente so 10 s; resposta do modelo passa disso e vira 502")


def agente_e_componente_do_framework():
    """4.4 - o agente tambem E um componente, nao so consome componentes."""
    interfaces = (BIB / "framework" / "interfaces.py").read_text(encoding="utf-8")
    assert "class IComponenteAgente" in interfaces, "falta IComponenteAgente"
    for metodo in ("def perguntar", "def redigir_aviso"):
        assert metodo in interfaces, "IComponenteAgente sem {0}".format(metodo)

    componentes = (BIB / "framework" / "componentes.py").read_text(encoding="utf-8")
    assert "class ComponenteAgenteHTTP" in componentes, "falta ComponenteAgenteHTTP"


def app_do_framework_orquestra_o_agente():
    """4.4 - o agente e orquestrado pelo Template Method, nao por fora dele."""
    app = (BIB / "apps" / "app_aviso_vencimento.py").read_text(encoding="utf-8")
    assert "FrameworkBiblioteca" in app, "a app nao estende o framework"
    assert "ComponenteAgenteHTTP" in app, "a app nao registra o componente do agente"
    for gancho in ("def pre_processar", "def executar_logica", "def pos_processar"):
        assert gancho in app, "a app nao implementa {0}".format(gancho)
    assert "def executar_operacao" not in app, (
        "a app sobrescreveu executar_operacao; o fluxo e do framework")
    assert "import httpx" not in sem_comentarios(app), (
        "a app fala HTTP direto em vez de usar os componentes")


def redator_de_aviso_nao_faz_conta():
    """4.3 - a regra de multa mora no servico de contratos, nao no prompt.

    O agente escreve a prosa; os numeros vem apurados de quem chamou. Se o
    prompt deixar o modelo calcular, a regra passa a existir em dois lugares.
    """
    fonte = (BIB / "services" / "agente" / "agente.py").read_text(encoding="utf-8")
    assert "INSTRUCOES_AVISO" in fonte, "falta o prompt do redator de avisos"
    inicio = fonte.index("INSTRUCOES_AVISO")
    prompt = fonte[inicio:inicio + 1200]
    assert "NÃO faça contas" in prompt, (
        "o prompt do aviso nao proibe o modelo de calcular valores")
    assert "Não invente" in prompt, (
        "o prompt do aviso nao proibe o modelo de inventar fatos")


def aviso_sai_mesmo_com_agente_fora(ctx):
    """4.3 - resiliencia: o aviso e a funcao, o agente e o acabamento.

    Roda a app com AGENTE_URL apontando para porta morta, entao o caminho do
    modelo e impossivel -- com ou sem credencial, e sem gastar nada na API.
    """
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    auth = ctx["auth"]

    r = c.post("/imoveis/imoveis/", headers=auth, json={
        "titulo": "Imovel para aviso", "tipo": "casa",
        "endereco": "Rua do Aviso, 1", "cidade": "Maceio",
        "quartos": 2, "banheiros": 1, "area_m2": 70.0, "valor_mensal": 1200.0,
    })
    assert r.status_code == 201, r.text
    imovel_id = r.json()["id"]

    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 1, "imovel_id": imovel_id, "meses": 1})
    assert r.status_code == 201, r.text

    ambiente = dict(os.environ)
    ambiente["AGENTE_URL"] = "http://127.0.0.1:9"
    saida = subprocess.run(
        [sys.executable, "apps/app_aviso_vencimento.py", "--dias", "31"],
        cwd=str(BIB), env=ambiente, capture_output=True, text=True, timeout=180,
    )
    assert saida.returncode == 0, "a app falhou:" + chr(10) + saida.stdout + saida.stderr
    assert "texto padr" in saida.stdout, (
        "a app nao caiu no texto padrao com o agente fora:" + chr(10) + saida.stdout)
    assert "enviado(s)" in saida.stdout, saida.stdout

    r = c.get("/notificacoes/notificacoes/usuario/1", headers=auth)
    assert r.status_code == 200, r.text
    assert any(n["imovel_id"] == imovel_id for n in r.json()), (
        "o aviso nao virou notificacao para o imovel {0}".format(imovel_id))


def suite_de_testes_passa():
    """6.1 - a suite de unidade e parte do ritual, nao um anexo.

    Roda so os testes de unidade: sao rapidos e nao precisam de servico no ar.
    Os de integracao ficam de fora porque as checagens vivas deste validador ja
    cobrem o mesmo caminho, com bancos temporarios.
    """
    saida = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=300,
    )
    assert saida.returncode == 0, (
        "a suite de testes falhou:" + chr(10) + saida.stdout[-3000:] + saida.stderr[-1000:]
    )


def diagramas_refletem_o_codigo():
    """6.3 - diagrama em texto, versionado, e sem PNG do dominio antigo."""
    pasta = RAIZ / "diagramas"
    assert not list(pasta.glob("*.png")), (
        "voltaram PNGs: os antigos eram do dominio de biblioteca")

    esperados = {"1_arquitetura.md", "2_componentes.md", "3_framework.md",
                 "4_contrato.md", "5_agente.md", "README.md"}
    presentes = {p.name for p in pasta.glob("*.md")}
    assert esperados <= presentes, (
        "faltam diagramas: {0}".format(sorted(esperados - presentes)))

    for arquivo in pasta.glob("[0-9]_*.md"):
        texto = arquivo.read_text(encoding="utf-8")
        assert "```mermaid" in texto, (
            "{0} nao tem diagrama Mermaid".format(arquivo.name))


def documentacao_sem_lastro_do_projeto_antigo():
    """6.4/6.5 - os docs descrevem o que existe, nao o trabalho anterior."""
    docs = ["README.md", "COMO_CRIAR_APP.md", "scrum.md"]
    problemas = []
    for nome in docs:
        caminho = RAIZ / nome
        assert caminho.exists(), "falta {0}".format(nome)
        texto = caminho.read_text(encoding="utf-8")
        for linha in texto.splitlines():
            if "tes-rds" in linha:
                continue
            for termo in ("Biblioteca Online", "acervo de livros", "LPS",
                          "seed_emprestimos", "COMO_DERIVAR_PRODUTO"):
                if termo in linha:
                    problemas.append("{0}: {1}".format(nome, termo))
    assert not problemas, "resíduo do projeto antigo: " + ", ".join(problemas)

    assert not (RAIZ / "COMO_DERIVAR_PRODUTO.md").exists(), (
        "COMO_DERIVAR_PRODUTO.md voltou; a LPS era da disciplina anterior")


def links_dos_docs_apontam_para_arquivos_que_existem():
    """Link quebrado em README é o tipo de erro que só aparece na correção."""
    import re as _re

    problemas = []
    for doc in list(RAIZ.glob("*.md")) + list((RAIZ / "diagramas").glob("*.md")):
        texto = doc.read_text(encoding="utf-8")
        for alvo in _re.findall(r"\]\(([^)#:]+\.(?:md|py|txt|jsx|js))\)", texto):
            destino = (doc.parent / alvo).resolve()
            if not destino.exists():
                problemas.append("{0} -> {1}".format(doc.name, alvo))
    assert not problemas, "link quebrado: " + ", ".join(problemas)


def segredo_do_token_fora_do_codigo():
    """Revisão de código: o segredo que assina token estava no repositório.

    Com ele qualquer um forjava login de qualquer usuário. Agora vem de
    TOKEN_SECRET ou é gerado uma vez e guardado no usuarios.db.
    """
    for caminho, texto in _fontes_py():
        assert "biblioteca_secret" not in texto, (
            "o segredo antigo voltou em {0}".format(caminho.relative_to(RAIZ)))

    main_usuarios = (BIB / "services" / "usuarios" / "main.py").read_text(encoding="utf-8")
    assert not re.search(r"SECRET\s*=\s*[\"']", main_usuarios), (
        "usuarios/main.py voltou a ter segredo literal")
    assert "TOKEN_SECRET" in main_usuarios, "o segredo do token não vem de TOKEN_SECRET"

    seguranca = (BIB / "services" / "usuarios" / "security.py").read_text(encoding="utf-8")
    assert "pbkdf2_hmac" in seguranca, "a senha não usa hash lento com sal"
    assert "hmac.new" in seguranca, "o token não é assinado com HMAC"


def cadastro_publico_nao_cria_admin(ctx):
    """Revisão de código: qualquer um se registrava como admin pela rota
    pública, e qualquer usuário logado alterava o cadastro de outro."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)

    r = c.post("/usuarios/usuarios/registro", json={
        "nome": "Intruso", "email": "intruso@teste.br",
        "senha": "senha123", "tipo": "admin",
    })
    assert r.status_code == 403, (
        "segundo admin pela rota pública deveria dar 403, deu {0} {1}"
        .format(r.status_code, r.text))

    r = c.post("/usuarios/usuarios/registro", json={
        "nome": "Comum", "email": "comum@teste.br",
        "senha": "senha123", "tipo": "inquilino",
    })
    assert r.status_code == 201, r.text
    r = c.post("/usuarios/usuarios/login",
               json={"email": "comum@teste.br", "senha": "senha123"})
    token_comum = {"Authorization": r.json()["token"]}

    r = c.patch("/usuarios/usuarios/1", headers=token_comum, json={"ativo": False})
    assert r.status_code == 403, (
        "usuário comum desativou o admin: deveria dar 403, deu {0}"
        .format(r.status_code))

    r = c.post("/usuarios/usuarios/login",
               json={"email": "validador@teste.br", "senha": "senha123"})
    assert r.status_code == 200, "o admin perdeu o acesso: " + r.text


def filtro_de_cidade_ignora_acento(ctx):
    """Revisão de código: 'Maceió' não achava o que estava gravado como
    'Maceio', o que quebrava o exemplo principal da tela do agente."""
    base = GATEWAY + "/imoveis/imoveis/"
    sem = httpx.get(base, headers=ctx["auth"], params={"cidade": "Maceio"}, timeout=10.0)
    com = httpx.get(base, headers=ctx["auth"], params={"cidade": "Maceió"}, timeout=10.0)
    assert sem.status_code == com.status_code == 200
    ids_sem = {i["id"] for i in sem.json()}
    assert ids_sem, "o fluxo deveria ter cadastrado um imóvel em Maceio"
    assert {i["id"] for i in com.json()} == ids_sem, (
        "'Maceió' e 'Maceio' devolveram imóveis diferentes")


def atraso_usa_a_data_local():
    """Revisão: o SQL comparava com date('now') do SQLite (UTC), enquanto a
    multa usa a data local; em UTC-3, entre 21h e meia-noite, o contrato
    aparecia atrasado com multa zero."""
    repo = (BIB / "services" / "contratos" / "repository.py").read_text(encoding="utf-8")
    assert "date('now')" not in repo, "marcar_atrasados voltou a usar a data UTC do SQLite"


def _novo_inquilino(c, email):
    r = c.post("/usuarios/usuarios/registro", json={
        "nome": email.split("@")[0], "email": email,
        "senha": "senha123", "tipo": "inquilino",
    })
    assert r.status_code == 201, r.text
    usuario_id = r.json()["id"]
    r = c.post("/usuarios/usuarios/login", json={"email": email, "senha": "senha123"})
    return usuario_id, {"Authorization": r.json()["token"]}


def contrato_so_para_o_dono(ctx):
    """Revisão: qualquer usuário logado lia e encerrava contrato de outro.

    Inclui a tentativa de se passar por admin mandando os headers de
    identidade direto: o gateway descarta os do cliente e põe os verdadeiros.
    """
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    dono_id, token_dono = _novo_inquilino(c, "dono@teste.br")
    _, token_outro = _novo_inquilino(c, "outro@teste.br")

    r = c.post("/imoveis/imoveis/", headers=ctx["auth"], json={
        "titulo": "Imovel do dono", "tipo": "casa", "endereco": "Rua D, 1",
        "cidade": "Recife", "quartos": 2, "banheiros": 1,
        "area_m2": 70.0, "valor_mensal": 1500.0,
    })
    imovel_id = r.json()["id"]

    r = c.post("/contratos/contratos/", headers=token_dono,
               json={"inquilino_id": dono_id, "imovel_id": imovel_id})
    assert r.status_code == 201, "o dono não conseguiu assinar: " + r.text
    contrato_id = r.json()["id"]

    listados = {x["id"] for x in c.get("/contratos/contratos/", headers=token_outro).json()}
    assert contrato_id not in listados, "outro inquilino viu o contrato na listagem"

    r = c.get(f"/contratos/contratos/{contrato_id}", headers=token_outro)
    assert r.status_code == 404, "outro inquilino leu o contrato: {0}".format(r.status_code)

    r = c.post(f"/contratos/contratos/{contrato_id}/encerrar", headers=token_outro)
    assert r.status_code == 404, "outro inquilino encerrou o contrato: {0}".format(r.status_code)

    forjado = dict(token_outro, **{"X-Usuario-Id": str(dono_id), "X-Usuario-Tipo": "admin"})
    r = c.get(f"/contratos/contratos/{contrato_id}", headers=forjado)
    assert r.status_code == 404, (
        "header de identidade forjado pelo cliente passou pelo gateway: {0}".format(r.status_code))

    r = c.post("/contratos/contratos/", headers=token_outro,
               json={"inquilino_id": dono_id, "imovel_id": imovel_id})
    assert r.status_code == 403, "assinou em nome de outro: {0}".format(r.status_code)

    r = c.get(f"/contratos/contratos/{contrato_id}", headers=token_dono)
    assert r.status_code == 200, "o próprio dono perdeu acesso: " + r.text


def aviso_nao_se_repete(ctx):
    """Revisão: rodar a App de aviso duas vezes mandava o mesmo aviso duas vezes."""
    ambiente = dict(os.environ)
    ambiente["AGENTE_URL"] = "http://127.0.0.1:9"
    saida = subprocess.run(
        [sys.executable, "apps/app_aviso_vencimento.py", "--dias", "31"],
        cwd=str(BIB), env=ambiente, capture_output=True, text=True, timeout=180,
    )
    assert saida.returncode == 0, saida.stdout + saida.stderr
    assert "0 enviado(s)" in saida.stdout, (
        "a segunda execução reenviou avisos:" + chr(10) + saida.stdout)
    assert "pulado(s)" in saida.stdout and "0 pulado(s)" not in saida.stdout, (
        "a segunda execução não reconheceu os avisos já enviados:" + chr(10) + saida.stdout)


def proprietario_so_por_promocao(ctx):
    """Revisão: o cadastro público aceitava proprietário, e qualquer pessoa
    ganhava acesso ao portfólio se cadastrando com esse perfil."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    r = c.post("/usuarios/usuarios/registro", json={
        "nome": "Falso", "email": "falso-dono@teste.br",
        "senha": "senha123", "tipo": "proprietario",
    })
    assert r.status_code == 403, "proprietário pela rota pública: {0}".format(r.status_code)

    usuario_id, token = _novo_inquilino(c, "futuro-dono@teste.br")
    r = c.patch("/usuarios/usuarios/{0}".format(usuario_id), headers=token,
                json={"tipo": "proprietario"})
    assert r.status_code == 403, "inquilino se promoveu: {0}".format(r.status_code)

    r = c.patch("/usuarios/usuarios/{0}".format(usuario_id), headers=ctx["auth"],
                json={"tipo": "proprietario"})
    assert r.status_code == 200, "admin não conseguiu promover: " + r.text

    r = c.post("/imoveis/imoveis/", headers=token, json=NOVO_IMOVEL)
    assert r.status_code == 201, "proprietário promovido não cadastra imóvel: " + r.text


def gateway_reaproveita_conexoes():
    """Revisão: o /health consultava os serviços um por um, e cada requisição
    abria e fechava um cliente HTTP novo."""
    gateway = BIB / "gateway"
    proxy = sem_comentarios((gateway / "proxy.py").read_text(encoding="utf-8"))
    auth = sem_comentarios((gateway / "auth.py").read_text(encoding="utf-8"))
    for nome, fonte in (("proxy.py", proxy), ("auth.py", auth)):
        assert "async with httpx.AsyncClient" not in fonte, (
            nome + " voltou a abrir um cliente HTTP por requisição")
    assert "asyncio.gather" in proxy, "o /health voltou a consultar em série"


def reload_nao_deixa_orfaos():
    """Revisão: no Windows, com --reload, o terminate() matava só o processo
    pai do uvicorn e o filho ficava segurando a porta."""
    fonte = sem_comentarios((RAIZ / "subir_servicos.py").read_text(encoding="utf-8"))
    assert "taskkill" in fonte and '"/T"' in fonte, (
        "subir_servicos.py não derruba a árvore de processos no Windows")


NOVO_IMOVEL = {
    "titulo": "Imovel de teste", "tipo": "casa", "endereco": "Rua T, 1",
    "cidade": "Penedo", "quartos": 2, "banheiros": 1,
    "area_m2": 70.0, "valor_mensal": 1400.0,
}


def imovel_so_quem_administra(ctx):
    """Revisão: qualquer usuário logado cadastrava, alterava e removia imóvel."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    _, inquilino = _novo_inquilino(c, "curioso@teste.br")
    url = "/imoveis/imoveis/{0}".format(ctx["imovel_id"])

    tentativas = [
        ("cadastrar", c.post("/imoveis/imoveis/", headers=inquilino, json=NOVO_IMOVEL)),
        ("alterar", c.patch(url, headers=inquilino, json={"valor_mensal": 1.0})),
        ("remover", c.delete(url, headers=inquilino)),
        ("mudar disponibilidade", c.patch(url + "/disponibilidade", headers=inquilino,
                                          params={"disponivel": False})),
        ("cadastrar com header forjado", c.post(
            "/imoveis/imoveis/", json=NOVO_IMOVEL,
            headers=dict(inquilino, **{"X-Usuario-Tipo": "admin"}))),
    ]
    for acao, r in tentativas:
        assert r.status_code == 403, "inquilino conseguiu {0}: {1}".format(acao, r.status_code)

    r = c.post("/imoveis/imoveis/", headers=ctx["auth"], json=NOVO_IMOVEL)
    assert r.status_code == 201, "admin perdeu o cadastro: " + r.text


def encerrar_nao_fica_preso(ctx):
    """Revisão: encerrar falhava se o imóvel já estivesse livre, e o contrato
    não fechava nunca mais; e liberava o imóvel antes de gravar o encerramento."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    auth = ctx["auth"]
    imovel_id = c.post("/imoveis/imoveis/", headers=auth, json=NOVO_IMOVEL).json()["id"]
    r = c.post("/contratos/contratos/", headers=auth,
               json={"inquilino_id": 1, "imovel_id": imovel_id})
    assert r.status_code == 201, r.text
    contrato_id = r.json()["id"]

    r = c.delete("/imoveis/imoveis/{0}".format(imovel_id), headers=auth)
    assert r.status_code == 400, "removeu imóvel alugado: {0}".format(r.status_code)

    r = c.patch("/imoveis/imoveis/{0}/disponibilidade".format(imovel_id),
                headers=auth, params={"disponivel": True})
    assert r.status_code == 200, r.text

    r = c.post("/contratos/contratos/{0}/encerrar".format(contrato_id), headers=auth)
    assert r.status_code == 200, "contrato preso com o imóvel já livre: " + r.text
    assert r.json()["status"] == "encerrado"


def email_repetido_da_400(ctx):
    """Revisão: trocar o e-mail por um que já existe estourava 500."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    _novo_inquilino(c, "primeiro@teste.br")
    segundo_id, segundo = _novo_inquilino(c, "segundo@teste.br")
    r = c.patch("/usuarios/usuarios/{0}".format(segundo_id), headers=segundo,
                json={"email": "primeiro@teste.br"})
    assert r.status_code == 400, "e-mail repetido deu {0}".format(r.status_code)


def recomenda_onde_ja_morou(ctx):
    """Revisão: quem já tinha morado num imóvel nunca mais o via recomendado."""
    c = httpx.Client(base_url=GATEWAY, timeout=20.0)
    morador_id, morador = _novo_inquilino(c, "morador@teste.br")
    imovel_id = c.post("/imoveis/imoveis/", headers=ctx["auth"], json=NOVO_IMOVEL).json()["id"]
    r = c.post("/contratos/contratos/", headers=morador,
               json={"inquilino_id": morador_id, "imovel_id": imovel_id})
    assert r.status_code == 201, r.text
    r = c.post("/contratos/contratos/{0}/encerrar".format(r.json()["id"]), headers=morador)
    assert r.status_code == 200, r.text

    r = c.get("/recomendacao/recomendacao/{0}".format(morador_id), headers=morador,
              params={"limite": 500})
    assert r.status_code == 200, r.text
    assert imovel_id in [x["imovel_id"] for x in r.json()], (
        "o imóvel do contrato encerrado sumiu da recomendação")


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
    ("10", "pagina de imoveis substituiu o catalogo", pagina_de_imoveis_substituiu_catalogo),
    ("10", "frontend nao inventa dados", frontend_nao_inventa_dados),
    ("11", "pagina de contratos substituiu emprestimos", pagina_de_contratos_substituiu_emprestimos),
    ("11", "tela nao duplica a regra de multa", tela_nao_duplica_a_regra_de_multa),
    ("12", "configurador foi removido", configurador_foi_removido),
    ("12", "frontend sem vocabulario de biblioteca", frontend_sem_vocabulario_de_biblioteca),
    ("13", "agente usa a camada de componentes", agente_usa_a_camada_de_componentes),
    ("13", "ferramentas do agente sao de leitura", ferramentas_do_agente_sao_de_leitura),
    ("13", "agente usa modelo atual", agente_usa_modelo_atual),
    ("rev", "agente aceita Gemini ou Claude", agente_aceita_gemini_ou_claude),
    ("14", "agente e componente do framework", agente_e_componente_do_framework),
    ("14", "app do framework orquestra o agente", app_do_framework_orquestra_o_agente),
    ("14", "redator de aviso nao faz conta", redator_de_aviso_nao_faz_conta),
    ("10", "frontend compila", frontend_compila),
    ("16", "diagramas refletem o codigo", diagramas_refletem_o_codigo),
    ("16", "documentacao sem lastro do projeto antigo", documentacao_sem_lastro_do_projeto_antigo),
    ("16", "links dos docs existem", links_dos_docs_apontam_para_arquivos_que_existem),
    ("rev", "segredo do token fora do codigo", segredo_do_token_fora_do_codigo),
    ("rev", "atraso usa a data local", atraso_usa_a_data_local),
    ("rev", "gateway reaproveita conexoes", gateway_reaproveita_conexoes),
    ("rev", "reload nao deixa orfaos", reload_nao_deixa_orfaos),
    ("15", "suite de testes passa", suite_de_testes_passa),
    ("-", "todo .py compila", tudo_compila),
]

VIVAS = [
    ("2", "health geral com os 7 no ar", health_geral),
    ("2", "fluxo completo pelo gateway", fluxo_completo_pelo_gateway),
    ("2", "resposta comprimida intacta", resposta_comprimida_chega_intacta),
    ("2", "rota protegida exige token", rota_protegida_exige_token),
    ("4", "filtros de imovel filtram", filtros_de_imovel),
    ("4", "disponibilidade e booleana", disponibilidade_e_booleana),
    ("8", "ciclo de contrato completo", ciclo_de_contrato),
    ("8", "um contrato aberto por imovel", um_contrato_aberto_por_imovel),
    ("12", "recomendacao responde rapido", recomendacao_responde_rapido),
    ("13", "agente degrada sem credencial", agente_degrada_sem_credencial),
    ("14", "aviso sai mesmo com agente fora", aviso_sai_mesmo_com_agente_fora),
    ("rev", "cadastro publico nao cria admin", cadastro_publico_nao_cria_admin),
    ("rev", "filtro de cidade ignora acento", filtro_de_cidade_ignora_acento),
    ("rev", "contrato so para o dono", contrato_so_para_o_dono),
    ("rev", "aviso nao se repete", aviso_nao_se_repete),
    ("rev", "imovel so quem administra", imovel_so_quem_administra),
    ("rev", "encerrar nao fica preso", encerrar_nao_fica_preso),
    ("rev", "email repetido da 400", email_repetido_da_400),
    ("rev", "recomenda onde ja morou", recomenda_onde_ja_morou),
    ("rev", "proprietario so por promocao", proprietario_so_por_promocao),
]


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
            print("  [ok]    bloco 2  shutdown liberou as {0} portas".format(len(PORTAS)))
        shutil.rmtree(pasta, ignore_errors=True)

    return relatorio(falhas)


if __name__ == "__main__":
    sys.exit(main())
