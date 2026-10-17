import httpx
from fastapi import Request, Response

from config import ServiceRegistry
from exceptions import ServicoNaoEncontrado, ServicoIndisponivel


class ProxyService:

    HEADERS_NAO_REPASSADOS = frozenset({
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    })

    HEADERS_DE_IDENTIDADE = frozenset({"x-usuario-id", "x-usuario-tipo"})

    def __init__(self, registry: ServiceRegistry, timeout: float = 10.0):
        self._registry = registry
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

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.request(
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

    def __init__(self, registry: ServiceRegistry, timeout: float = 3.0):
        self._registry = registry
        self._timeout = timeout

    async def verificar(self) -> dict:
        resultados = {}
        async with httpx.AsyncClient() as client:
            for nome, info in self._registry.itens():
                try:
                    resp = await client.get(
                        f"{info['url']}/health", timeout=self._timeout
                    )
                    resultados[nome] = {
                        "status": "ok" if resp.status_code == 200 else "erro",
                        "porta": info["porta"],
                    }
                except httpx.RequestError:
                    resultados[nome] = {
                        "status": "indisponivel",
                        "porta": info["porta"],
                    }

        todos_ok = all(s["status"] == "ok" for s in resultados.values())
        return {
            "gateway": "ok",
            "status_geral": "ok" if todos_ok else "degradado",
            "servicos": resultados,
        }
