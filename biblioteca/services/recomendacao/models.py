from pydantic import BaseModel


class ImovelRecomendado(BaseModel):
    imovel_id: int
    titulo: str
    tipo: str
    cidade: str
    score: float
    motivo: str


class PerfilUsuario(BaseModel):
    usuario_id: int
    tipos_favoritos: list[str]
    cidades_favoritas: list[str]
    total_contratos: int