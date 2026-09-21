import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import RecomendacaoRepository
from clients import EmprestimoClient, CatalogoClient
from service import RecomendacaoService
from routes import criar_router
from exceptions import ServicoIndisponivel

DB_PATH = os.getenv("RECOMENDACAO_DB", "recomendacao.db")
EMPRESTIMOS_URL = os.getenv("EMPRESTIMOS_URL", "http://localhost:8003")
CATALOGO_URL = os.getenv("CATALOGO_URL", "http://localhost:8001")

database = Database(DB_PATH)
repository = RecomendacaoRepository(database)
emprestimo_client = EmprestimoClient(EMPRESTIMOS_URL)
catalogo_client = CatalogoClient(CATALOGO_URL)
service = RecomendacaoService(repository, emprestimo_client, catalogo_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_schema()
    yield


app = FastAPI(
    title="Biblioteca Online — Recomendação",
    description="Recomendação de livros baseada no perfil e histórico do usuário",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServicoIndisponivel)
def tratar_servico_indisponivel(request: Request, exc: ServicoIndisponivel):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "recomendacao", "status": "ok", "port": 8005}