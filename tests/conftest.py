"""Infra dos testes.

Problema que este arquivo resolve: cada microsserviço usa imports planos
(`from models import ...`), porque cada um roda com o uvicorn a partir da sua
própria pasta. Isso é proposital e está documentado no CLAUDE.md -- mas
significa que `models`, `service` e `repository` são nomes que COLIDEM em
`sys.modules` quando mais de um serviço é importado no mesmo processo pytest.

`carregar` isola isso: limpa os nomes do cache, aponta o sys.path para a pasta
do serviço, importa, e limpa de novo. Os objetos devolvidos continuam válidos
depois, porque guardam referência aos próprios módulos.
"""
import importlib
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
BIB = RAIZ / "biblioteca"

NOMES_COMUNS = (
    "models", "service", "repository", "database",
    "exceptions", "clients", "routes", "main", "security",
)


def _limpar_cache():
    for nome in NOMES_COMUNS:
        sys.modules.pop(nome, None)


def carregar(servico: str, *modulos: str):
    """Importa módulos de um serviço, isolando o cache de nomes.

    Devolve um módulo só, ou uma tupla quando se pede mais de um.
    """
    caminho = str(BIB / "services" / servico)
    _limpar_cache()
    sys.path.insert(0, caminho)
    try:
        carregados = [importlib.import_module(m) for m in modulos]
    finally:
        sys.path.remove(caminho)
        _limpar_cache()
    return carregados[0] if len(carregados) == 1 else tuple(carregados)


def carregar_framework(*modulos: str):
    caminho = str(BIB / "framework")
    for nome in ("framework", "interfaces", "componentes"):
        sys.modules.pop(nome, None)
    sys.path.insert(0, caminho)
    try:
        carregados = [importlib.import_module(m) for m in modulos]
    finally:
        sys.path.remove(caminho)
    return carregados[0] if len(carregados) == 1 else tuple(carregados)


class RepositorioFake:
    """Base dos repositórios fake: guarda registros em memória.

    Existe para os testes de serviço não tocarem em SQLite. A camada de serviço
    é onde mora a regra de negócio, e é ela que queremos exercitar.
    """

    def __init__(self, registros=None):
        self.registros = list(registros or [])
        self.gravacoes = []

    def _proximo_id(self):
        return max((r.id for r in self.registros), default=0) + 1


@pytest.fixture
def sem_rede(monkeypatch):
    """Garante que nenhum teste de unidade faça chamada HTTP de verdade."""
    import httpx

    def proibido(*args, **kwargs):
        raise AssertionError("teste de unidade tentou falar HTTP de verdade")

    for metodo in ("get", "post", "patch", "put", "delete", "request"):
        monkeypatch.setattr(httpx, metodo, proibido, raising=False)
