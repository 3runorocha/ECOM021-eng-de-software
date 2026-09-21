import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from database import Database
from repository import UsuarioRepository
from security import PasswordHasher, TokenService
from service import UsuarioService
from routes import criar_router
from exceptions import (
    UsuarioNaoEncontrado, RegraDeNegocio,
    CredenciaisInvalidas, TokenInvalido,
)

DB_PATH = os.getenv("USUARIOS_DB", "usuarios.db")

SECRET = "biblioteca_secret_2025"

database = Database(DB_PATH)
repository = UsuarioRepository(database)
hasher = PasswordHasher(SECRET)
token_service = TokenService(SECRET)
service = UsuarioService(repository, hasher, token_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_schema()
    yield


app = FastAPI(
    title="Biblioteca Online — Usuários",
    description="Registro, autenticação e gerenciamento de perfis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(UsuarioNaoEncontrado)
def tratar_nao_encontrado(request: Request, exc: UsuarioNaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra_de_negocio(request: Request, exc: RegraDeNegocio):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(CredenciaisInvalidas)
def tratar_credenciais(request: Request, exc: CredenciaisInvalidas):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(TokenInvalido)
def tratar_token_invalido(request: Request, exc: TokenInvalido):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


app.include_router(criar_router(service))


@app.get("/health")
def health():
    return {"service": "usuarios", "status": "ok", "port": 8002}
