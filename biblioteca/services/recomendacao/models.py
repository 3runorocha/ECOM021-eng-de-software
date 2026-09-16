from pydantic import BaseModel


class LivroRecomendado(BaseModel):
    livro_id: int
    titulo: str
    autor: str
    genero: str
    score: float
    motivo: str


class PerfilUsuario(BaseModel):
    usuario_id: int
    generos_favoritos: list[str]
    autores_favoritos: list[str]
    total_emprestimos: int