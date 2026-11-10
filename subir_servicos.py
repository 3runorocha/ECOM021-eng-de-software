#!/usr/bin/env python
"""Sobe o API Gateway e os 6 microsservicos em um unico comando.

    python subir_servicos.py            # normal
    python subir_servicos.py --reload   # recarrega ao salvar (desenvolvimento)

Ctrl+C encerra todos. Se algum servico morrer, o script derruba o resto e
avisa qual foi -- silenciosamente ficar com 6 de 7 no ar e mais confuso do
que falhar de uma vez.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent / "biblioteca"
ARQUIVO_ENV = Path(__file__).resolve().parent / ".env"


def ler_env(caminho: Path) -> dict:
    """Le um .env simples (CHAVE=valor por linha), sem depender de biblioteca.

    Linhas vazias, linhas que comecam com # e linhas sem = sao ignoradas; aspas
    em volta do valor sao removidas. Valor vazio e tratado como ausente.
    """
    valores = {}
    if not caminho.exists():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:
            valores[chave.strip()] = valor
    return valores

SERVICOS = [
    ("imoveis",      RAIZ / "services" / "imoveis",      8001),
    ("usuarios",     RAIZ / "services" / "usuarios",     8002),
    ("contratos",    RAIZ / "services" / "contratos",    8003),
    ("notificacoes", RAIZ / "services" / "notificacoes", 8004),
    ("recomendacao", RAIZ / "services" / "recomendacao", 8005),
    ("agente",       RAIZ / "services" / "agente",       8006),
    ("gateway",      RAIZ / "gateway",                   8000),
]


def iniciar(reload: bool) -> list:
    processos = []
    for nome, pasta, porta in SERVICOS:
        if not (pasta / "main.py").exists():
            encerrar(processos)
            sys.exit(f"[erro] nao encontrei {pasta / 'main.py'}")

        comando = [sys.executable, "-m", "uvicorn", "main:app", "--port", str(porta)]
        if reload:
            comando.append("--reload")

        processo = subprocess.Popen(comando, cwd=pasta)
        processos.append((nome, porta, processo))
        print(f"  {nome:<13} :{porta}   pid {processo.pid}")
    return processos


def derrubar(processo: subprocess.Popen) -> None:
    """Encerra o processo junto com os filhos dele.

    Com --reload o uvicorn serve a porta num processo filho. No Windows o
    terminate() mata so o pai, e o filho fica orfao segurando a porta ate
    alguem matar na mao; o taskkill /T derruba a arvore inteira.
    """
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
            capture_output=True,
        )
    else:
        processo.terminate()


def encerrar(processos: list) -> None:
    for nome, _porta, processo in processos:
        if processo.poll() is None:
            derrubar(processo)
    for nome, _porta, processo in processos:
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"  {nome} nao respondeu ao terminate, matando")
            processo.kill()


def main() -> int:
    reload = "--reload" in sys.argv

    do_env = ler_env(ARQUIVO_ENV)
    for chave, valor in do_env.items():
        os.environ.setdefault(chave, valor)
    if do_env:
        print("Lido .env: " + ", ".join(sorted(do_env)))

    print("Subindo os servicos" + (" (--reload)" if reload else "") + ":")
    processos = iniciar(reload)
    print("\nGateway:  http://localhost:8000")
    print("Swagger:  http://localhost:8000/docs")
    print("Health:   http://localhost:8000/health")
    print("\nCtrl+C encerra todos.\n")

    codigo = 0
    try:
        while True:
            for nome, porta, processo in processos:
                if processo.poll() is not None:
                    print(
                        f"\n[!] '{nome}' (:{porta}) encerrou com codigo "
                        f"{processo.returncode}. Derrubando os outros."
                    )
                    return 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        encerrar(processos)

    return codigo


if __name__ == "__main__":
    sys.exit(main())
