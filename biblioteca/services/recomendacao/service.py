from collections import Counter

from models import LivroRecomendado, PerfilUsuario
from repository import RecomendacaoRepository
from clients import EmprestimoClient, CatalogoClient


class RecomendacaoService:

    PONTOS_GENERO = 3
    PONTOS_AUTOR = 2
    PENALIDADE_JA_EMPRESTADO = 10
    PENALIDADE_JA_RECOMENDADO = 5
    TOP_N_PREFERENCIAS = 3

    def __init__(
        self,
        repository: RecomendacaoRepository,
        emprestimos: EmprestimoClient,
        catalogo: CatalogoClient,
    ):
        self._repo = repository
        self._emprestimos = emprestimos
        self._catalogo = catalogo

    def obter_perfil(self, usuario_id: int) -> PerfilUsuario:
        historico = self._emprestimos.buscar_historico(usuario_id)

        if not historico:
            return PerfilUsuario(
                usuario_id=usuario_id,
                generos_favoritos=[],
                autores_favoritos=[],
                total_emprestimos=0,
            )

        generos, autores = self._coletar_preferencias(historico)
        return PerfilUsuario(
            usuario_id=usuario_id,
            generos_favoritos=self._mais_frequentes(generos),
            autores_favoritos=self._mais_frequentes(autores),
            total_emprestimos=len(historico),
        )

    def recomendar(self, usuario_id: int, limite: int = 5) -> list[LivroRecomendado]:
        historico = self._emprestimos.buscar_historico(usuario_id)
        catalogo = self._catalogo.buscar_catalogo_completo()

        ids_emprestados = {emp["livro_id"] for emp in historico}
        generos, autores = self._coletar_preferencias(historico)
        top_generos = set(self._mais_frequentes(generos))
        top_autores = set(self._mais_frequentes(autores))
        ja_recomendados = self._repo.listar_recomendados(usuario_id)

        recomendacoes = []
        for livro in catalogo:
            recomendado = self._pontuar(
                livro, top_generos, top_autores,
                ids_emprestados, ja_recomendados,
            )
            if recomendado is not None:
                recomendacoes.append(recomendado)

        recomendacoes.sort(key=lambda r: r.score, reverse=True)
        resultado = recomendacoes[:limite]

        self._repo.registrar_recomendacoes(
            usuario_id, [rec.livro_id for rec in resultado]
        )
        return resultado

    def _coletar_preferencias(self, historico: list[dict]) -> tuple[list, list]:
        generos, autores = [], []
        for emp in historico:
            livro = self._catalogo.buscar_livro(emp["livro_id"])
            if livro:
                generos.append(livro["genero"])
                autores.append(livro["autor"])
        return generos, autores

    def _mais_frequentes(self, valores: list[str]) -> list[str]:
        return [v for v, _ in Counter(valores).most_common(self.TOP_N_PREFERENCIAS)]

    def _pontuar(
        self,
        livro: dict,
        top_generos: set,
        top_autores: set,
        ids_emprestados: set,
        ja_recomendados: set,
    ) -> LivroRecomendado | None:
        if livro.get("quantidade_disponivel", 0) <= 0:
            return None

        score = 0.0
        motivo = []

        if livro["genero"] in top_generos:
            score += self.PONTOS_GENERO
            motivo.append(f"gênero '{livro['genero']}' está entre seus favoritos")

        if livro["autor"] in top_autores:
            score += self.PONTOS_AUTOR
            motivo.append(f"autor '{livro['autor']}' está entre seus favoritos")

        if livro["id"] in ids_emprestados:
            score -= self.PENALIDADE_JA_EMPRESTADO

        if livro["id"] in ja_recomendados:
            score -= self.PENALIDADE_JA_RECOMENDADO

        if score <= 0:
            return None

        return LivroRecomendado(
            livro_id=livro["id"],
            titulo=livro["titulo"],
            autor=livro["autor"],
            genero=livro["genero"],
            score=score,
            motivo=" e ".join(motivo) if motivo else "recomendação geral",
        )