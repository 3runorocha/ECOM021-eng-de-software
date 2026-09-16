import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import (
    ComponenteCatalogoHTTP,
    ComponenteEmprestimoHTTP,
    ComponenteNotificacaoHTTP,
)


class AppEmprestimo(FrameworkBiblioteca):

    def configurar_componentes(self) -> None:
        self.registrar_componente("catalogo",     ComponenteCatalogoHTTP())
        self.registrar_componente("emprestimos",  ComponenteEmprestimoHTTP())
        self.registrar_componente("notificacoes", ComponenteNotificacaoHTTP())

    def get_campos_obrigatorios(self) -> list[str]:
        return ["usuario_id", "livro_id"]

    def pre_processar(self, contexto: dict) -> None:
        catalogo = self.get_componente("catalogo")
        livro_id = contexto["livro_id"]

        livros = catalogo.buscar_livros({})
        livro = next((l for l in livros if l["id"] == livro_id), None)

        if not livro:
            raise ValueError(f"Livro ID {livro_id} não encontrado no catálogo")

        if livro["quantidade_disponivel"] <= 0:
            raise ValueError(
                f"Livro '{livro['titulo']}' não possui exemplares disponíveis no momento"
            )

        contexto["titulo_livro"] = livro["titulo"]

    def executar_logica(self, contexto: dict) -> dict:
        emprestimos = self.get_componente("emprestimos")
        return emprestimos.realizar_emprestimo(
            contexto["usuario_id"],
            contexto["livro_id"],
        )

    def pos_processar(self, contexto: dict, resultado: dict) -> None:
        notificacoes = self.get_componente("notificacoes")
        titulo = contexto.get("titulo_livro", f"ID {contexto['livro_id']}")
        prazo  = resultado.get("data_devolucao_prevista", "—")

        notificacoes.enviar(
            usuario_id=contexto["usuario_id"],
            tipo="reserva_confirmada",
            mensagem=(
                f"Empréstimo confirmado! Livro: '{titulo}'. "
                f"Devolução prevista: {prazo}. Evite multas devolvendo no prazo."
            ),
            livro_id=contexto["livro_id"],
        )

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        try:
            notificacoes = self.get_componente("notificacoes")
            notificacoes.enviar(
                usuario_id=contexto.get("usuario_id", 0),
                tipo="atraso",
                mensagem=f"Não foi possível realizar o empréstimo: {str(erro)}",
                livro_id=contexto.get("livro_id"),
            )
        except Exception:
            pass

        return {"erro": True, "mensagem": str(erro), "tipo": type(erro).__name__}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="App 1 — Empréstimo com Notificação")
    parser.add_argument("--usuario", type=int, default=1, help="ID do usuário")
    parser.add_argument("--livro",   type=int, required=True, help="ID do livro")
    args = parser.parse_args()

    print("=" * 60)
    print("APP 1 — Empréstimo com Notificação Automática")
    print("=" * 60)

    app = AppEmprestimo()
    resultado = app.executar_operacao({
        "usuario_id": args.usuario,
        "livro_id":   args.livro,
    })

    print(f"\nResultado: {resultado}")
    print(f"\nLog de execução:")
    for entrada in app.get_log():
        print(f"  {entrada}")