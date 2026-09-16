from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import LivroRepository
from service import CatalogoService
from routes import criar_router
from exceptions import LivroNaoEncontrado, RegraDeNegocio

DB_PATH = "catalogo.db"

database = Database(DB_PATH)
repository = LivroRepository(database)
service = CatalogoService(repository)

app = FastAPI(
    title="Biblioteca Online — Catálogo",
    description="Gerenciamento do acervo de livros da biblioteca",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    database.init_schema()


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