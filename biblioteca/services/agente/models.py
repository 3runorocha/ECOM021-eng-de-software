from typing import Optional
from pydantic import BaseModel, Field


class Pergunta(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)
    inquilino_id: Optional[int] = None


class FerramentaUsada(BaseModel):
    ferramenta: str
    argumentos: dict


class PedidoAviso(BaseModel):
    fatos: dict = Field(min_length=1)


class Aviso(BaseModel):
    mensagem: str
    modelo: str


class ImovelResumo(BaseModel):
    id: int
    titulo: str
    tipo: str
    cidade: str
    endereco: str
    quartos: int
    banheiros: int
    area_m2: float
    valor_mensal: float


class Resposta(BaseModel):
    resposta: str
    ferramentas_usadas: list[FerramentaUsada]
    modelo: str
    truncado: bool
    imoveis: list[ImovelResumo] = []
