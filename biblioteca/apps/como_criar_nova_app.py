import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import (
    ComponenteEmprestimoHTTP,
    ComponenteNotificacaoHTTP,
)


class AppDevolucao(FrameworkBiblioteca):

    def configurar_componentes(self) -> None:
        self.registrar_componente("emprestimos",  ComponenteEmprestimoHTTP())
        self.registrar_componente("notificacoes", ComponenteNotificacaoHTTP())

    def executar_logica(self, contexto: dict) -> dict:
        emprestimos   = self.get_componente("emprestimos")
        emprestimo_id = contexto["emprestimo_id"]

        return emprestimos.realizar_devolucao(emprestimo_id)

    def get_campos_obrigatorios(self) -> list[str]:
        return ["emprestimo_id", "usuario_id"]

    def pos_processar(self, contexto: dict, resultado: dict) -> None:
        notificacoes = self.get_componente("notificacoes")
        multa        = resultado.get("multa", 0)
        livro_id     = resultado.get("livro_id")

        if multa > 0:
            mensagem = (
                f"Devolução registrada com atraso. "
                f"Multa a pagar: R$ {multa:.2f}. "
                f"Dirija-se à biblioteca para quitar o débito."
            )
            tipo = "atraso"
        else:
            mensagem = "Devolução realizada no prazo. Obrigado!"
            tipo     = "reserva_confirmada"

        notificacoes.enviar(
            usuario_id=contexto["usuario_id"],
            tipo=tipo,
            mensagem=mensagem,
            livro_id=livro_id,
        )

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        return {
            "erro":          True,
            "mensagem":      str(erro),
            "emprestimo_id": contexto.get("emprestimo_id"),
            "sugestao":      "Verifique se o empréstimo existe e não foi devolvido anteriormente.",
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nova App — Devolução com Multa")
    parser.add_argument("--emprestimo", type=int, required=True, help="ID do empréstimo")
    parser.add_argument("--usuario",    type=int, required=True, help="ID do usuário")
    args = parser.parse_args()

    print("=" * 60)
    print("NOVA APP — Devolução com Multa e Notificação")
    print("=" * 60)

    app = AppDevolucao()
    resultado = app.executar_operacao({
        "emprestimo_id": args.emprestimo,
        "usuario_id":    args.usuario,
    })

    print(f"\nResultado da devolução: {resultado}")
    print(f"\nLog automático do framework:")
    for entrada in app.get_log():
        print(f"  Operação: {entrada['operacao']}")
        print(f"  Status:   {entrada['status']}")
        print(f"  Duração:  {entrada['duracao_segundos']}s")
        print(f"  Timestamp:{entrada['timestamp']}")