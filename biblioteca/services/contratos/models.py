from typing import Optional
from pydantic import BaseModel, Field

STATUS_EM_ABERTO = ("ativo", "atrasado")


class Chamador(BaseModel):
    id: int
    tipo: str

    @property
    def admin(self) -> bool:
        return self.tipo == "admin"


class ContratoCreate(BaseModel):
    inquilino_id: int
    imovel_id: int
    meses: Optional[int] = Field(default=None, ge=1, le=120)


class Contrato(BaseModel):
    id: int
    inquilino_id: int
    imovel_id: int
    data_inicio: str
    data_fim_prevista: str
    data_fim_real: Optional[str]
    valor_mensal: float
    status: str
    multa: float
