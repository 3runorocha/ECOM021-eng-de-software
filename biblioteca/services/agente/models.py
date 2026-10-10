from typing import Optional
from pydantic import BaseModel, Field


class Pergunta(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    inquilino_id: Optional[int] = None


class FerramentaUsada(BaseModel):
    ferramenta: str
    argumentos: dict


class PedidoAviso(BaseModel):
    # Fatos ja apurados por quem chamou. O agente nao busca nada aqui: so
    # redige. Dict aberto porque a aplicacao decide o que e relevante citar.
    fatos: dict = Field(min_length=1)


class Aviso(BaseModel):
    mensagem: str
    modelo: str


class Resposta(BaseModel):
    resposta: str
    ferramentas_usadas: list[FerramentaUsada]
    modelo: str
    truncado: bool
