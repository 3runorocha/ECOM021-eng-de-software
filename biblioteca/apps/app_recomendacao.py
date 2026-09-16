import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import (
    ComponenteCatalogoHTTP,
    ComponenteEmprestimoHTTP,
    ComponenteRecomendacaoHTTP,
)


class AppRecomendacao(FrameworkBiblioteca):

    def configurar_componentes(self) -> None:
        self.registrar_componente("catalogo",     ComponenteCatalogoHTTP())
        self.registrar_componente("emprestimos",  ComponenteEmprestimoHTTP())
        self.registrar_componente("recomendacao", ComponenteRecomendacaoHTTP())

    def get_campos_obrigatorios(self) -> list[str]:
        return ["usuario_id"]

    def pre_processar(self, contexto: dict) -> None:
        recomendacao = self.get_componente("recomendacao")
        usuario_id   = contexto["usuario_id"]

        perfil = recomendacao.obter_perfil(usuario_id)
        contexto["perfil"] = perfil

        if perfil["total_emprestimos"] == 0:
            contexto["_aviso"] = (
                "Usuário sem histórico de empréstimos. "
                "Recomendações baseadas em popularidade geral."
            )

    def executar_logica(self, contexto: dict) -> dict:
        recomendacao = self.get_componente("recomendacao")
        limite       = contexto.get("limite", 5)
        usuario_id   = contexto["usuario_id"]

        livros = recomendacao.recomendar(usuario_id, limite)

        return {
            "usuario_id":    usuario_id,
            "perfil":        contexto.get("perfil", {}),
            "recomendacoes": livros,
            "total":         len(livros),
            "aviso":         contexto.get("_aviso"),
        }

    def pos_processar(self, contexto: dict, resultado: dict) -> None:
        emprestimos = self.get_componente("emprestimos")
        historico   = emprestimos.listar_emprestimos(contexto["usuario_id"])

        resultado["historico_recente"] = historico[-5:] if historico else []

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        try:
            catalogo = self.get_componente("catalogo")
            livros   = catalogo.buscar_livros({})
            fallback = [
                {
                    "livro_id": l["id"],
                    "titulo":   l["titulo"],
                    "autor":    l["autor"],
                    "genero":   l["genero"],
                    "score":    0.0,
                    "motivo":   "recomendação por disponibilidade (fallback)",
                }
                for l in livros[:5]
                if l.get("quantidade_disponivel", 0) > 0
            ]
            return {
                "usuario_id":    contexto.get("usuario_id"),
                "recomendacoes": fallback,
                "total":         len(fallback),
                "erro":          str(erro),
                "fallback":      True,
            }
        except Exception:
            return {"erro": True, "mensagem": str(erro), "tipo": type(erro).__name__}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="App 2 — Recomendação Personalizada")
    parser.add_argument("--usuario", type=int, default=1, help="ID do usuário")
    parser.add_argument("--limite",  type=int, default=5, help="Quantidade de recomendações")
    args = parser.parse_args()

    print("=" * 60)
    print("APP 2 — Recomendação Personalizada com Perfil")
    print("=" * 60)

    app = AppRecomendacao()
    resultado = app.executar_operacao({
        "usuario_id": args.usuario,
        "limite":     args.limite,
    })

    print(f"\nPerfil do usuário: {resultado.get('perfil')}")
    print(f"\nRecomendações ({resultado.get('total')} livros):")
    for rec in resultado.get("recomendacoes", []):
        print(f"  [{rec['score']}pts] {rec['titulo']} — {rec['motivo']}")

    if resultado.get("aviso"):
        print(f"\nAviso: {resultado['aviso']}")

    print(f"\nLog de execução:")
    for entrada in app.get_log():
        print(f"  {entrada}")