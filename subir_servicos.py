#!/usr/bin/env python
"""Sobe o API Gateway e os 5 microsservicos em um unico comando.

    python subir_servicos.py            # normal
    python subir_servicos.py --reload   # recarrega ao salvar (desenvolvimento)

Ctrl+C encerra todos. Se algum servico morrer, o script derruba o resto e
avisa qual foi -- silenciosamente ficar com 5 de 6 no ar e mais confuso do
que falhar de uma vez.
"""
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent / "biblioteca"

# O gateway vem por ultimo: ele so procura os servicos quando recebe uma
# requisicao, mas subir na ordem deixa o log mais legivel.
SERVICOS = [
    ("catalogo",     RAIZ / "services" / "catalogo",     8001),
    ("usuarios",     RAIZ / "services" / "usuarios",     8002),
    ("emprestimos",  RAIZ / "services" / "emprestimos",  8003),
    ("notificacoes", RAIZ / "services" / "notificacoes", 8004),
    ("recomendacao", RAIZ / "services" / "recomendacao", 8005),
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


def encerrar(processos: list) -> None:
    for nome, _porta, processo in processos:
        if processo.poll() is None:
            processo.terminate()
    for nome, _porta, processo in processos:
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"  {nome} nao respondeu ao terminate, matando")
            processo.kill()


def main() -> int:
    reload = "--reload" in sys.argv

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
