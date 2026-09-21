import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import LivroRepository
from service import CatalogoService
from routes import criar_router
from exceptions import LivroNaoEncontrado, RegraDeNegocio

DB_PATH = os.getenv("CATALOGO_DB", "catalogo.db")

database = Database(DB_PATH)
repository = LivroRepository(database)
service = CatalogoService(repository)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_schema()
    yield


app = FastAPI(
    title="Biblioteca Online — Catálogo",
    description="Gerenciamento do acervo de livros da biblioteca",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LivroNaoEncontrado)
def tratar_nao_encontrado(request: Request, exc: LivroNaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra_de_negocio(request: Request, exc: RegraDeNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "catalogo", "status": "ok", "port": 8001}