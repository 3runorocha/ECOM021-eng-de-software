import os

import httpx
from interfaces import (
    IComponenteImovel,
    IComponenteUsuario,
    IComponenteContrato,
    IComponenteNotificacao,
    IComponenteAgente,
    IComponenteRecomendacao,
)


URL_IMOVEIS      = os.getenv("IMOVEIS_URL",      "http://127.0.0.1:8001")
URL_USUARIOS     = os.getenv("USUARIOS_URL",     "http://127.0.0.1:8002")
URL_CONTRATOS    = os.getenv("CONTRATOS_URL",    "http://127.0.0.1:8003")
URL_NOTIFICACOES = os.getenv("NOTIFICACOES_URL", "http://127.0.0.1:8004")
URL_RECOMENDACAO = os.getenv("RECOMENDACAO_URL", "http://127.0.0.1:8005")
URL_AGENTE       = os.getenv("AGENTE_URL",       "http://127.0.0.1:8006")


class ComponenteImovelHTTP(IComponenteImovel):

    def __init__(self, base_url: str = URL_IMOVEIS):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "imoveis"

    def buscar_imoveis(self, filtros: dict = None) -> list[dict]:
        params = filtros or {}
        resp = self._client.get(f"{self._url}/imoveis/", params=params)
        resp.raise_for_status()
        return resp.json()

    def cadastrar_imovel(self, dados: dict) -> dict:
        resp = self._client.post(f"{self._url}/imoveis/", json=dados)
        resp.raise_for_status()
        return resp.json()

    def definir_disponibilidade(self, imovel_id: int, disponivel: bool) -> None:
        resp = self._client.patch(
            f"{self._url}/imoveis/{imovel_id}/disponibilidade",
            params={"disponivel": disponivel},
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


class ComponenteContratoHTTP(IComponenteContrato):

    def __init__(self, base_url: str = URL_CONTRATOS):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        self._client = httpx.Client(timeout=30.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "contratos"

    def registrar_contrato(self, inquilino_id: int, imovel_id: int) -> dict:
        resp = self._client.post(
            f"{self._url}/contratos/",
            json={"inquilino_id": inquilino_id, "imovel_id": imovel_id},
        )
        resp.raise_for_status()
        return resp.json()

    def encerrar_contrato(self, contrato_id: int) -> dict:
        resp = self._client.post(f"{self._url}/contratos/{contrato_id}/encerrar")
        resp.raise_for_status()
        return resp.json()

    def listar_contratos(self, inquilino_id: int = None) -> list[dict]:
        params = {} if inquilino_id is None else {"inquilino_id": inquilino_id}
        resp = self._client.get(f"{self._url}/contratos/", params=params)
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

    def enviar(self, usuario_id: int, tipo: str, mensagem: str, imovel_id: int = None) -> dict:
        resp = self._client.post(
            f"{self._url}/notificacoes/",
            json={
                "usuario_id": usuario_id,
                "tipo": tipo,
                "mensagem": mensagem,
                "imovel_id": imovel_id,
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

class ComponenteAgenteHTTP(IComponenteAgente):

    def __init__(self, base_url: str = URL_AGENTE):
        self._url    = base_url
        self._client = None

    def inicializar(self) -> None:
        # O agente pensa antes de responder: timeout maior que o dos demais.
        self._client = httpx.Client(timeout=120.0)

    def finalizar(self) -> None:
        if self._client:
            self._client.close()

    def get_nome(self) -> str:
        return "agente"

    def perguntar(self, texto: str, inquilino_id: int = None) -> dict:
        corpo = {"texto": texto}
        if inquilino_id is not None:
            corpo["inquilino_id"] = inquilino_id
        resp = self._client.post(f"{self._url}/agente/perguntar", json=corpo)
        resp.raise_for_status()
        return resp.json()

    def redigir_aviso(self, fatos: dict) -> str:
        resp = self._client.post(
            f"{self._url}/agente/redigir-aviso", json={"fatos": fatos}
        )
        resp.raise_for_status()
        return resp.json()["mensagem"]
