from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agente import Agente
from ferramentas import imoveis, contratos
from routes import criar_router
from exceptions import AgenteIndisponivel, RegraDeNegocio

agente = Agente()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Os componentes abrem o cliente HTTP aqui e fecham no shutdown -- é o
    # mesmo ciclo de vida que as apps do framework usam.
    imoveis.inicializar()
    contratos.inicializar()
    yield
    imoveis.finalizar()
    contratos.finalizar()


app = FastAPI(
    title="Aluguel de Imóveis — Agente",
    description=(
        "Busca conversacional sobre o portfólio. Usa a camada de componentes "
        "do framework como ferramentas do modelo."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AgenteIndisponivel)
def tratar_indisponivel(request: Request, exc: AgenteIndisponivel):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra_de_negocio(request: Request, exc: RegraDeNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(criar_router(agente))


@app.get("/health")
def health():
    # O serviço fica "ok" mesmo sem credencial: ele sobe e responde. Quem quer
    # saber se o agente consegue pensar consulta /agente/status.
    return {"service": "agente", "status": "ok", "port": 8006}
