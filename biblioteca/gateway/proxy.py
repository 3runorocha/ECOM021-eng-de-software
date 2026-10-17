import asyncio
from http.cookiejar import CookieJar, DefaultCookiePolicy

import httpx
from fastapi import Request, Response

from config import ServiceRegistry
from exceptions import ServicoNaoEncontrado, ServicoIndisponivel


def novo_cliente_http(transport=None) -> httpx.AsyncClient:
    """Cliente único do gateway, reaproveitando as conexões com os serviços.

    Por ser compartilhado entre todos os usuários, ele não guarda cookie: um
    Set-Cookie vindo de um serviço não pode ir parar na requisição de outra
    pessoa.
    """
    sem_cookies = CookieJar(policy=DefaultCookiePolicy(allowed_domains=[]))
    return httpx.AsyncClient(cookies=sem_cookies, transport=transport)


class ProxyService:

    HEADERS_NAO_REPASSADOS = frozenset({
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    })

    HEADERS_DE_IDENTIDADE = frozenset({"x-usuario-id", "x-usuario-tipo"})

    def __init__(
        self, registry: ServiceRegistry, client: httpx.AsyncClient,
        timeout: float = 10.0,
    ):
        self._registry = registry
        self._client = client
        self._timeout = timeout

    async def encaminhar(
        self, request: Request, service_name: str, path: str
    ) -> Response:
        if service_name not in self._registry:
            raise ServicoNaoEncontrado(f"Servico '{service_name}' nao encontrado")

        target_url = f"{self._registry.url(service_name)}/{path}"
        params = dict(request.query_params)
        body = await request.body()
        headers = {
            chave: valor
            for chave, valor in request.headers.items()
            if chave.lower() != "host"
            and chave.lower() not in self.HEADERS_DE_IDENTIDADE
        }
        identidade = getattr(request.state, "identidade", None)
        if identidade:
            headers["x-usuario-id"] = str(identidade["usuario_id"])
            headers["x-usuario-tipo"] = identidade["tipo"]

        try:
            resp = await self._client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=params,
                content=body,
                timeout=self._timeout,
            )
        except httpx.RequestError:
            raise ServicoIndisponivel(
                f"Microsservico '{service_name}' indisponivel"
            )

        headers_resposta = {
            chave: valor
            for chave, valor in resp.headers.items()
            if chave.lower() not in self.HEADERS_NAO_REPASSADOS
        }

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=headers_resposta,
            media_type=resp.headers.get("content-type"),
        )


class MonitorServicos:

    def __init__(
        self, registry: ServiceRegistry, client: httpx.AsyncClient,
        timeout: float = 3.0,
    ):
        self._registry = registry
        self._client = client
        self._timeout = timeout

    async def _consultar(self, info: dict) -> dict:
        try:
            resp = await self._client.get(
                f"{info['url']}/health", timeout=self._timeout
            )
            status = "ok" if resp.status_code == 200 else "erro"
        except httpx.RequestError:
            status = "indisponivel"
        return {"status": status, "porta": info["porta"]}

    async def verificar(self) -> dict:
        """Consulta todos os serviços ao mesmo tempo.

        Em série, com um serviço fora do ar o /health levava o timeout dele
        somado ao dos outros; em paralelo, leva o do mais lento.
        """
        itens = list(self._registry.itens())
        estados = await asyncio.gather(*(self._consultar(info) for _, info in itens))
        resultados = {nome: estado for (nome, _), estado in zip(itens, estados)}

        todos_ok = all(s["status"] == "ok" for s in resultados.values())
        return {
            "gateway": "ok",
            "status_geral": "ok" if todos_ok else "degradado",
            "servicos": resultados,
        }
