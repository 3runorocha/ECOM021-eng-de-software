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
    PENALIDADE_JA_MOROU = 2
    PENALIDADE_JA_RECOMENDADO = 1
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

        por_id = self._indexar(self._imoveis.buscar_portfolio_completo())
        tipos, cidades = self._coletar_preferencias(historico, por_id)
        return PerfilUsuario(
            usuario_id=usuario_id,
            tipos_favoritos=self._mais_frequentes(tipos),
            cidades_favoritas=self._mais_frequentes(cidades),
            total_contratos=len(historico),
        )

    def recomendar(self, usuario_id: int, limite: int = 5) -> list[ImovelRecomendado]:
        historico = self._contratos.buscar_historico(usuario_id)
        portfolio = self._imoveis.buscar_portfolio_completo()

        em_aberto = {c["imovel_id"] for c in historico if c.get("status") != "encerrado"}
        ja_morou = {c["imovel_id"] for c in historico} - em_aberto
        tipos, cidades = self._coletar_preferencias(historico, self._indexar(portfolio))
        top_tipos = set(self._mais_frequentes(tipos))
        top_cidades = set(self._mais_frequentes(cidades))
        ja_recomendados = self._repo.listar_recomendados(usuario_id)

        recomendacoes = []
        for imovel in portfolio:
            if imovel["id"] in em_aberto:
                continue
            recomendado = self._pontuar(
                imovel, top_tipos, top_cidades,
                ja_morou, ja_recomendados,
            )
            if recomendado is not None:
                recomendacoes.append(recomendado)

        recomendacoes.sort(key=lambda r: r.score, reverse=True)
        resultado = recomendacoes[:limite]

        self._repo.registrar_recomendacoes(
            usuario_id, [rec.imovel_id for rec in resultado]
        )
        return resultado

    @staticmethod
    def _indexar(portfolio: list[dict]) -> dict:
        return {imovel["id"]: imovel for imovel in portfolio}

    def _coletar_preferencias(
        self, historico: list[dict], por_id: dict
    ) -> tuple[list, list]:
        """Tipo e cidade de cada imóvel do histórico.

        Sai do portfólio já carregado, não de uma chamada HTTP por contrato.
        """
        tipos, cidades = [], []
        for contrato in historico:
            imovel = por_id.get(contrato["imovel_id"])
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
        ja_morou: set,
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

        if imovel["id"] in ja_morou:
            score -= self.PENALIDADE_JA_MOROU
            motivo.append("você já morou aqui")

        if imovel["id"] in ja_recomendados:
            score -= self.PENALIDADE_JA_RECOMENDADO

        if score <= 0:
            return None

        return ImovelRecomendado(
            imovel_id=imovel["id"],
            titulo=imovel["titulo"],
            tipo=imovel["tipo"],
            cidade=imovel["cidade"],
            valor_mensal=imovel["valor_mensal"],
            score=score,
            motivo=" e ".join(motivo) if motivo else "recomendação geral",
        )
