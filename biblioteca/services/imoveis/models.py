from typing import Literal, Optional
from pydantic import BaseModel, Field

TipoImovel = Literal["apartamento", "casa"]


class ImovelCreate(BaseModel):
    titulo: str
    tipo: TipoImovel
    endereco: str
    cidade: str
    quartos: int = Field(ge=0)
    banheiros: int = Field(ge=0)
    area_m2: float = Field(gt=0)
    valor_mensal: float = Field(gt=0)


class ImovelUpdate(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[TipoImovel] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    quartos: Optional[int] = Field(default=None, ge=0)
    banheiros: Optional[int] = Field(default=None, ge=0)
    area_m2: Optional[float] = Field(default=None, gt=0)
    valor_mensal: Optional[float] = Field(default=None, gt=0)


class Imovel(BaseModel):
    id: int
    titulo: str
    tipo: TipoImovel
    endereco: str
    cidade: str
    quartos: int
    banheiros: int
    area_m2: float
    valor_mensal: float
    # Um imovel e unico: ou esta livre para alugar, ou nao esta. Diferente do
    # acervo de biblioteca, que tinha N exemplares do mesmo titulo.
    disponivel: bool
