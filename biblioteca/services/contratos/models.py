from typing import Optional
from pydantic import BaseModel, Field

# ativo    -> em vigor, dentro do prazo
# atrasado -> passou da data prevista e ainda nao foi encerrado
# encerrado-> imovel devolvido (com ou sem multa)
STATUS_EM_ABERTO = ("ativo", "atrasado")


class ContratoCreate(BaseModel):
    inquilino_id: int
    imovel_id: int
    # Prazo em meses. Ausente, usa ContratoService.PRAZO_MESES.
    meses: Optional[int] = Field(default=None, ge=1, le=120)


class Contrato(BaseModel):
    id: int
    inquilino_id: int
    imovel_id: int
    data_inicio: str
    data_fim_prevista: str
    data_fim_real: Optional[str]
    # Valor acordado na assinatura. Fica gravado no contrato porque o aluguel do
    # imovel pode mudar depois, e a multa se calcula sobre o valor contratado.
    valor_mensal: float
    status: str
    multa: float
