"""O que a suíte e a demonstração compartilham: endereços, contas de exemplo,
login e a cópia dos bancos.

O backend é o mesmo para tudo que roda aqui: um caso que assina contrato
mudaria o banco dos seguintes. Por isso os bancos são copiados antes e
restaurados depois, e o sistema termina exatamente como estava.
"""
import os
import sqlite3
import tempfile
from pathlib import Path

import httpx

RAIZ = Path(__file__).resolve().parent
SERVICOS = RAIZ.parent / "biblioteca" / "services"
BANCOS = ["imoveis", "usuarios", "contratos", "notificacoes", "recomendacao"]
FRONT = os.getenv("FRONT_URL", "http://127.0.0.1:5173")
GATEWAY = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000")
RESULTADOS = RAIZ / "resultados"

CONTAS = {
    "admin": ("admin@alugue.br", "admin123"),
    "beatriz": ("beatriz@alugue.br", "senha123"),
    "ana": ("ana@alugue.br", "senha123"),
    "joao": ("joao@alugue.br", "senha123"),
}


class AmbienteInvalido(Exception):
    pass


def conferir_ambiente() -> None:
    """Recusa rodar se faltar serviço, frontend ou os dados de exemplo."""
    try:
        saude = httpx.get(f"{GATEWAY}/health", timeout=5).json()
        httpx.get(FRONT, timeout=5).raise_for_status()
    except (httpx.HTTPError, ValueError):
        raise AmbienteInvalido(
            f"Sistema fora do ar. Suba os serviços (python subir_servicos.py) e o "
            f"frontend (npm run dev) antes: gateway {GATEWAY}, frontend {FRONT}.")
    if saude.get("status_geral") != "ok":
        raise AmbienteInvalido(f"Algum serviço está fora do ar: {saude.get('servicos')}")

    email, senha = CONTAS["admin"]
    r = httpx.post(f"{GATEWAY}/usuarios/usuarios/login",
                   json={"email": email, "senha": senha}, timeout=10)
    if r.status_code != 200:
        raise AmbienteInvalido("Admin do seed não encontrado: rode biblioteca/seed.py.")
    auth = {"Authorization": r.json()["token"]}
    imoveis = httpx.get(f"{GATEWAY}/imoveis/imoveis/", headers=auth, timeout=10).json()
    contratos = httpx.get(f"{GATEWAY}/contratos/contratos/", headers=auth, timeout=10).json()
    if len(imoveis) != 18 or len(contratos) != 42:
        raise AmbienteInvalido(
            f"São esperados os dados de exemplo (18 imóveis e 42 contratos); há "
            f"{len(imoveis)} e {len(contratos)}. Recrie os bancos com seed.py e "
            f"seed_contratos.py (veja o README desta pasta).")


def _copiar(origem: Path, destino: Path) -> None:
    with sqlite3.connect(origem) as src, sqlite3.connect(destino) as dst:
        src.backup(dst)


def copiar_bancos():
    """Copia os bancos agora e devolve a função que volta a eles."""
    pasta = Path(tempfile.mkdtemp(prefix="e2e-bancos-"))
    for nome in BANCOS:
        _copiar(SERVICOS / nome / f"{nome}.db", pasta / f"{nome}.db")

    def restaurar():
        for nome in BANCOS:
            _copiar(pasta / f"{nome}.db", SERVICOS / nome / f"{nome}.db")

    return restaurar


def entrar(page, conta: str, atraso: int = 0) -> None:
    email, senha = CONTAS[conta]
    page.goto(FRONT + "/")
    if atraso:
        page.locator("input[type=email]").press_sequentially(email, delay=atraso)
        page.locator("input[type=password]").press_sequentially(senha, delay=atraso)
    else:
        page.fill("input[type=email]", email)
        page.fill("input[type=password]", senha)
    page.click("button[type=submit]")
    page.locator("text=Sair").wait_for()


def ir(page, rota: str) -> None:
    page.goto(FRONT + rota)
    page.wait_for_load_state("networkidle")
