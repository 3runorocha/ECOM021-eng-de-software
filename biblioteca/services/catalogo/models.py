from typing import Optional
from pydantic import BaseModel


class LivroCreate(BaseModel):
    titulo: str
    autor: str
    isbn: str
    ano_publicacao: int
    genero: str
    quantidade_total: int


class LivroUpdate(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    genero: Optional[str] = None
    quantidade_total: Optional[int] = None


class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    isbn: str
    ano_publicacao: int
    genero: str
    quantidade_total: int
    quantidade_disponivel: int