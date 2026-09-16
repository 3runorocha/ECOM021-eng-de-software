import httpx
from fastapi import Request, Response

from config import ServiceRegistry
from exceptions import ServicoNaoEncontrado, ServicoIndisponivel


class ProxyService:

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
        headers = dict(request.headers)
        headers.pop("host", None)

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

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
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