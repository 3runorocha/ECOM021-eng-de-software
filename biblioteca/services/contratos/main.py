import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import ContratoRepository
from clients import ImovelClient
from service import ContratoService
from routes import criar_router
from exceptions import ContratoNaoEncontrado, RegraDeNegocio, ServicoIndisponivel

DB_PATH = os.getenv("CONTRATOS_DB", "contratos.db")
IMOVEIS_URL = os.getenv("IMOVEIS_URL", "http://localhost:8001")

database = Database(DB_PATH)
repository = ContratoRepository(database)
imovel_client = ImovelClient(IMOVEIS_URL)
service = ContratoService(repository, imovel_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_schema()
    yield


app = FastAPI(
    title="Aluguel de Imóveis — Contratos",
    description="Locação, encerramento e multa por atraso na desocupação",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ContratoNaoEncontrado)
def tratar_nao_encontrado(request: Request, exc: ContratoNaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra_de_negocio(request: Request, exc: RegraDeNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ServicoIndisponivel)
def tratar_servico_indisponivel(request: Request, exc: ServicoIndisponivel):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "contratos", "status": "ok", "port": 8003}
