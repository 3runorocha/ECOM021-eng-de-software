import httpx
from fastapi import Request, Response

from exceptions import GatewayError, TokenInvalido, ServicoIndisponivel


class AuthClient:

    def __init__(self, usuarios_url: str, timeout: float = 5.0):
        self._url = usuarios_url.rstrip("/")
        self._timeout = timeout

    async def validar_token(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self._url}/usuarios/validar-token",
                    headers={"authorization": token},
                    timeout=self._timeout,
                )
                if resp.status_code != 200:
                    raise TokenInvalido("Token invalido ou expirado")
                return resp.json()
            except httpx.RequestError:
                raise ServicoIndisponivel("Servico de autenticacao indisponivel")


class Autenticador:

    def __init__(self, auth_client: AuthClient, public_routes: set, rotas_livres: list):
        self._auth = auth_client
        self._public_routes = public_routes
        self._rotas_livres = rotas_livres

    def _e_rota_livre(self, path: str) -> bool:
        return any(path.startswith(r) for r in self._rotas_livres)

    async def processar(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if self._e_rota_livre(path):
            return await call_next(request)
        if method == "OPTIONS":
            return await call_next(request)
        if (method, path) in self._public_routes:
            return await call_next(request)

        token = request.headers.get("authorization", "")
        if not token:
            return Response(
                content='{"detail": "Token de autenticacao obrigatorio"}',
                status_code=401,
                media_type="application/json",
            )

        try:
            await self._auth.validar_token(token)
        except GatewayError as e:
            return Response(
                content=f'{{"detail": "{e.detail}"}}',
                status_code=e.status_code,
                media_type="application/json",
            )

        return await call_next(request)