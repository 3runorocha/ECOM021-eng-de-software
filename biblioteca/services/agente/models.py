from typing import Optional
from pydantic import BaseModel, Field


class Pergunta(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    inquilino_id: Optional[int] = None


class FerramentaUsada(BaseModel):
    ferramenta: str
    argumentos: dict


class Resposta(BaseModel):
    resposta: str
    ferramentas_usadas: list[FerramentaUsada]
    modelo: str
    truncado: bool
