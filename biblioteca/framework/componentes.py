import os

import httpx
from interfaces import (
    IComponenteCatalogo,
    IComponenteUsuario,
    IComponenteEmprestimo,
    IComponenteNotificacao,
    IComponenteRecomendacao,
)


URL_CATALOGO     = os.getenv("CATALOGO_URL",     "http://localhost:8001")
URL_USUARIOS     = os.getenv("USUARIOS_URL",     "http://localhost:8002")
URL_EMPRESTIMOS  = os.getenv("EMPRESTIMOS_URL",  "http://localhost:8003")
URL_NOTIFICACOES = os.getenv("NOTIFICACOES_URL", "http://localhost:8004")
URL_RECOMENDACAO = os.getenv("RECOMENDACAO_URL", "http://localhost:8005")


class ComponenteCatalogoHTTP(IComponenteCatalogo):

    def __init__(self, base_url: str = URL_CATALOGO):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "catalogo"

    def buscar_livros(self, filtros: dict = None) -> list[dict]:
        params = filtros or {}
        resp = self._client.get(f"{self._url}/livros/", params=params)
        resp.raise_for_status()
        return resp.json()

    def cadastrar_livro(self, dados: dict) -> dict:
        resp = self._client.post(f"{self._url}/livros/", json=dados)
        resp.raise_for_status()
        return resp.json()

    def atualizar_disponibilidade(self, livro_id: int, delta: int) -> None:
        resp = self._client.patch(
            f"{self._url}/livros/{livro_id}/disponibilidade",
            params={"delta": delta},
        )
        resp.raise_for_status()


class ComponenteUsuarioHTTP(IComponenteUsuario):

    def __init__(self, base_url: str = URL_USUARIOS):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "usuarios"

    def registrar(self, dados: dict) -> dict:
        resp = self._client.post(f"{self._url}/usuarios/registro", json=dados)
        resp.raise_for_status()
        return resp.json()

    def autenticar(self, email: str, senha: str) -> dict | None:
        resp = self._client.post(
            f"{self._url}/usuarios/login",
            json={"email": email, "senha": senha},
        )
        if resp.status_code == 401:
            return None
        resp.raise_for_status()
        return resp.json()

    def buscar_usuario(self, usuario_id: int) -> dict | None:
        resp = self._client.get(f"{self._url}/usuarios/{usuario_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


class ComponenteEmprestimoHTTP(IComponenteEmprestimo):

    def __init__(self, base_url: str = URL_EMPRESTIMOS):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "emprestimos"

    def realizar_emprestimo(self, usuario_id: int, livro_id: int) -> dict:
        resp = self._client.post(
            f"{self._url}/emprestimos/",
            json={"usuario_id": usuario_id, "livro_id": livro_id},
        )
        resp.raise_for_status()
        return resp.json()

    def realizar_devolucao(self, emprestimo_id: int) -> dict:
        resp = self._client.post(f"{self._url}/emprestimos/{emprestimo_id}/devolver")
        resp.raise_for_status()
        return resp.json()

    def listar_emprestimos(self, usuario_id: int) -> list[dict]:
        resp = self._client.get(
            f"{self._url}/emprestimos/",
            params={"usuario_id": usuario_id},
        )
        resp.raise_for_status()
        return resp.json()


class ComponenteNotificacaoHTTP(IComponenteNotificacao):

    def __init__(self, base_url: str = URL_NOTIFICACOES):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "notificacoes"

    def enviar(self, usuario_id: int, tipo: str, mensagem: str, livro_id: int = None) -> dict:
        resp = self._client.post(
            f"{self._url}/notificacoes/",
            json={
                "usuario_id": usuario_id,
                "tipo": tipo,
                "mensagem": mensagem,
                "livro_id": livro_id,
            },
        )
        resp.raise_for_status()
        return resp.json()

    def listar(self, usuario_id: int) -> list[dict]:
        resp = self._client.get(f"{self._url}/notificacoes/usuario/{usuario_id}")
        resp.raise_for_status()
        return resp.json()


class ComponenteRecomendacaoHTTP(IComponenteRecomendacao):

    def __init__(self, base_url: str = URL_RECOMENDACAO):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "recomendacao"

    def recomendar(self, usuario_id: int, limite: int = 5) -> list[dict]:
        resp = self._client.get(
            f"{self._url}/recomendacao/{usuario_id}",
            params={"limite": limite},
        )
        resp.raise_for_status()
        return resp.json()

    def obter_perfil(self, usuario_id: int) -> dict:
        resp = self._client.get(f"{self._url}/recomendacao/perfil/{usuario_id}")
        resp.raise_for_status()
        return resp.json()