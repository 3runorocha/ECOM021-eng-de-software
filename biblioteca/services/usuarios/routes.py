from fastapi import APIRouter, Header
from models import UsuarioCreate, UsuarioLogin, UsuarioPublico, UsuarioUpdate
from service import UsuarioService


def criar_router(service: UsuarioService) -> APIRouter:
    router = APIRouter(prefix="/usuarios", tags=["Usuários"])

    @router.post("/registro", response_model=UsuarioPublico, status_code=201)
    def registrar(usuario: UsuarioCreate):
        return service.registrar(usuario)

    @router.post("/login")
    def login(credenciais: UsuarioLogin):
        return service.login(credenciais)

    @router.get("/", response_model=list[UsuarioPublico])
    def listar_usuarios():
        return service.listar_usuarios()

    @router.get("/{usuario_id}", response_model=UsuarioPublico)
    def buscar_usuario(usuario_id: int):
        return service.buscar_usuario(usuario_id)

    @router.patch("/{usuario_id}", response_model=UsuarioPublico)
    def atualizar_usuario(usuario_id: int, dados: UsuarioUpdate):
        return service.atualizar_usuario(usuario_id, dados)

    @router.post("/validar-token")
    def validar(authorization: str = Header(...)):
        return service.validar_token(authorization)

    return router
