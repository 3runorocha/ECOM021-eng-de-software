from collections import Counter

from models import ImovelRecomendado, PerfilUsuario
from repository import RecomendacaoRepository
from clients import ContratoClient, ImovelClient


class RecomendacaoService:
    """Recomenda imoveis a partir do historico do usuario.

    O algoritmo e o mesmo do acervo de biblioteca, com as preferencias
    remapeadas para o dominio de aluguel: genero virou tipo (apartamento/casa)
    e autor virou cidade. Na Fase 4 este servico e substituido pelo agente,
    entao a pontuacao aqui e deliberadamente simples.
    """

    PONTOS_TIPO = 3
    PONTOS_CIDADE = 2
    PENALIDADE_JA_ALUGADO = 10
    PENALIDADE_JA_RECOMENDADO = 5
    TOP_N_PREFERENCIAS = 3

    def __init__(
        self,
        repository: RecomendacaoRepository,
        contratos: ContratoClient,
        imoveis: ImovelClient,
    ):
        self._repo = repository
        self._contratos = contratos
        self._imoveis = imoveis

    def obter_perfil(self, usuario_id: int) -> PerfilUsuario:
        historico = self._contratos.buscar_historico(usuario_id)

        if not historico:
            return PerfilUsuario(
                usuario_id=usuario_id,
                tipos_favoritos=[],
                cidades_favoritas=[],
                total_contratos=0,
            )

        tipos, cidades = self._coletar_preferencias(historico)
        return PerfilUsuario(
            usuario_id=usuario_id,
            tipos_favoritos=self._mais_frequentes(tipos),
            cidades_favoritas=self._mais_frequentes(cidades),
            total_contratos=len(historico),
        )

    def recomendar(self, usuario_id: int, limite: int = 5) -> list[ImovelRecomendado]:
        historico = self._contratos.buscar_historico(usuario_id)
        portfolio = self._imoveis.buscar_portfolio_completo()

        ids_alugados = {c["imovel_id"] for c in historico}
        tipos, cidades = self._coletar_preferencias(historico)
        top_tipos = set(self._mais_frequentes(tipos))
        top_cidades = set(self._mais_frequentes(cidades))
        ja_recomendados = self._repo.listar_recomendados(usuario_id)

        recomendacoes = []
        for imovel in portfolio:
            recomendado = self._pontuar(
                imovel, top_tipos, top_cidades,
                ids_alugados, ja_recomendados,
            )
            if recomendado is not None:
                recomendacoes.append(recomendado)

        recomendacoes.sort(key=lambda r: r.score, reverse=True)
        resultado = recomendacoes[:limite]

        self._repo.registrar_recomendacoes(
            usuario_id, [rec.imovel_id for rec in resultado]
        )
        return resultado

    def _coletar_preferencias(self, historico: list[dict]) -> tuple[list, list]:
        tipos, cidades = [], []
        for contrato in historico:
            imovel = self._imoveis.buscar_imovel(contrato["imovel_id"])
            if imovel:
                tipos.append(imovel["tipo"])
                cidades.append(imovel["cidade"])
        return tipos, cidades

    def _mais_frequentes(self, valores: list[str]) -> list[str]:
        return [v for v, _ in Counter(valores).most_common(self.TOP_N_PREFERENCIAS)]

    def _pontuar(
        self,
        imovel: dict,
        top_tipos: set,
        top_cidades: set,
        ids_alugados: set,
        ja_recomendados: set,
    ) -> ImovelRecomendado | None:
        if not imovel.get("disponivel", False):
            return None

        score = 0.0
        motivo = []

        if imovel["tipo"] in top_tipos:
            score += self.PONTOS_TIPO
            motivo.append(f"tipo '{imovel['tipo']}' está entre seus preferidos")

        if imovel["cidade"] in top_cidades:
            score += self.PONTOS_CIDADE
            motivo.append(f"cidade '{imovel['cidade']}' está entre suas preferidas")

        if imovel["id"] in ids_alugados:
            score -= self.PENALIDADE_JA_ALUGADO

        if imovel["id"] in ja_recomendados:
            score -= self.PENALIDADE_JA_RECOMENDADO

        if score <= 0:
            return None

        return ImovelRecomendado(
            imovel_id=imovel["id"],
            titulo=imovel["titulo"],
            tipo=imovel["tipo"],
            cidade=imovel["cidade"],
            score=score,
            motivo=" e ".join(motivo) if motivo else "recomendação geral",
        )
