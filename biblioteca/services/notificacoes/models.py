from typing import Optional
from pydantic import BaseModel


class NotificacaoCreate(BaseModel):
    usuario_id: int
    tipo: str
    mensagem: str
    livro_id: Optional[int] = None


class Notificacao(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    mensagem: str
    livro_id: Optional[int]
    lida: bool
    data_criacao: str