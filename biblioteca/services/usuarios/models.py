from typing import Literal, Optional
from pydantic import BaseModel

TipoUsuario = Literal["inquilino", "proprietario", "admin"]


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    tipo: TipoUsuario = "inquilino"


class UsuarioLogin(BaseModel):
    email: str
    senha: str


class UsuarioPublico(BaseModel):
    id: int
    nome: str
    email: str
    tipo: str
    ativo: bool


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    tipo: Optional[TipoUsuario] = None
    ativo: Optional[bool] = None
