from typing import Optional
from pydantic import BaseModel


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    tipo: str = "aluno"   # aluno | bibliotecario | admin


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
    tipo: Optional[str] = None
    ativo: Optional[bool] = None
