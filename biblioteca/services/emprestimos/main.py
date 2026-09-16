from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import EmprestimoRepository
from clients import CatalogoClient
from service import EmprestimoService
from routes import criar_router
from exceptions import EmprestimoNaoEncontrado, RegraDeNegocio, ServicoIndisponivel

DB_PATH = "emprestimos.db"
CATALOGO_URL = "http://localhost:8001"

database = Database(DB_PATH)
repository = EmprestimoRepository(database)
catalogo_client = CatalogoClient(CATALOGO_URL)
service = EmprestimoService(repository, catalogo_client)

app = FastAPI(
    title="Biblioteca Online — Empréstimos",
    description="Gerenciamento de empréstimos e devoluções de livros",
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


@app.exception_handler(EmprestimoNaoEncontrado)
def tratar_nao_encontrado(request: Request, exc: EmprestimoNaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra_de_negocio(request: Request, exc: RegraDeNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ServicoIndisponivel)
def tratar_servico_indisponivel(request: Request, exc: ServicoIndisponivel):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "emprestimos", "status": "ok", "port": 8003}