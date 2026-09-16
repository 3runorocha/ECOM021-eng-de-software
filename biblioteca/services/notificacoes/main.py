from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import NotificacaoRepository
from clients import EmprestimoClient
from service import NotificacaoService
from routes import criar_router
from exceptions import NotificacaoNaoEncontrada, ServicoIndisponivel

DB_PATH = "notificacoes.db"
EMPRESTIMOS_URL = "http://localhost:8003"

database = Database(DB_PATH)
repository = NotificacaoRepository(database)
emprestimo_client = EmprestimoClient(EMPRESTIMOS_URL)
service = NotificacaoService(repository, emprestimo_client)

app = FastAPI(
    title="Biblioteca Online — Notificações",
    description="Alertas de prazo, atraso e disponibilidade para usuários",
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


@app.exception_handler(NotificacaoNaoEncontrada)
def tratar_nao_encontrada(request: Request, exc: NotificacaoNaoEncontrada):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ServicoIndisponivel)
def tratar_servico_indisponivel(request: Request, exc: ServicoIndisponivel):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "notificacoes", "status": "ok", "port": 8004}