from typing import Optional
from pydantic import BaseModel


class EmprestimoCreate(BaseModel):
    usuario_id: int
    livro_id: int


class Emprestimo(BaseModel):
    id: int
    usuario_id: int
    livro_id: int
    data_emprestimo: str
    data_devolucao_prevista: str
    data_devolucao_real: Optional[str]
    status: str
    multa: float