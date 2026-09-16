from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import SERVICES, PUBLIC_ROUTES, ROTAS_LIVRES, ServiceRegistry
from auth import AuthClient, Autenticador
from proxy import ProxyService, MonitorServicos
from exceptions import GatewayError

registry = ServiceRegistry(SERVICES)
auth_client = AuthClient(registry.url("usuarios"))
autenticador = Autenticador(auth_client, PUBLIC_ROUTES, ROTAS_LIVRES)
proxy_service = ProxyService(registry)
monitor = MonitorServicos(registry)

app = FastAPI(
    title="Biblioteca Online - API Gateway",
    description="Ponto de entrada unico para todos os microsservicos da biblioteca",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(GatewayError)
async def tratar_gateway_error(request: Request, exc: GatewayError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.middleware("http")
async def middleware_autenticacao(request: Request, call_next):
    return await autenticador.processar(request, call_next)


METODOS = ["GET", "POST", "PATCH", "DELETE", "PUT"]


@app.api_route("/catalogo/{path:path}", methods=METODOS)
async def gateway_catalogo(request: Request, path: str):
    return await proxy_service.encaminhar(request, "catalogo", path)


@app.api_route("/usuarios/{path:path}", methods=METODOS)
async def gateway_usuarios(request: Request, path: str):
    return await proxy_service.encaminhar(request, "usuarios", path)


@app.api_route("/emprestimos/{path:path}", methods=METODOS)
async def gateway_emprestimos(request: Request, path: str):
    return await proxy_service.encaminhar(request, "emprestimos", path)


@app.api_route("/notificacoes/{path:path}", methods=METODOS)
async def gateway_notificacoes(request: Request, path: str):
    return await proxy_service.encaminhar(request, "notificacoes", path)


@app.api_route("/recomendacao/{path:path}", methods=METODOS)
async def gateway_recomendacao(request: Request, path: str):
    return await proxy_service.encaminhar(request, "recomendacao", path)


@app.get("/health")
async def health_check():
    return await monitor.verificar()


@app.get("/services")
def listar_servicos():
    return {
        "gateway": {"porta": 8000, "descricao": "API Gateway - ponto de entrada unico"},
        **{
            nome: {"porta": info["porta"], "descricao": info["descricao"]}
            for nome, info in registry.itens()
        },
    }