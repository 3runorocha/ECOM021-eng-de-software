import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import (
    ComponenteImovelHTTP,
    ComponenteContratoHTTP,
    ComponenteNotificacaoHTTP,
)


class AppContrato(FrameworkBiblioteca):

    def configurar_componentes(self) -> None:
        self.registrar_componente("imoveis",      ComponenteImovelHTTP())
        self.registrar_componente("contratos",    ComponenteContratoHTTP())
        self.registrar_componente("notificacoes", ComponenteNotificacaoHTTP())

    def get_campos_obrigatorios(self) -> list[str]:
        return ["inquilino_id", "imovel_id"]

    def pre_processar(self, contexto: dict) -> None:
        imoveis = self.get_componente("imoveis")
        imovel_id = contexto["imovel_id"]

        portfolio = imoveis.buscar_imoveis({})
        imovel = next((i for i in portfolio if i["id"] == imovel_id), None)

        if not imovel:
            raise ValueError(f"Imóvel ID {imovel_id} não encontrado no portfólio")

        if not imovel["disponivel"]:
            raise ValueError(
                f"Imóvel '{imovel['titulo']}' já possui contrato em aberto"
            )

        contexto["titulo_imovel"] = imovel["titulo"]
        contexto["valor_mensal"] = imovel["valor_mensal"]

    def executar_logica(self, contexto: dict) -> dict:
        contratos = self.get_componente("contratos")
        return contratos.registrar_contrato(
            contexto["inquilino_id"],
            contexto["imovel_id"],
        )

    def pos_processar(self, contexto: dict, resultado: dict) -> None:
        notificacoes = self.get_componente("notificacoes")
        titulo = contexto.get("titulo_imovel", f"ID {contexto['imovel_id']}")
        fim = resultado.get("data_fim_prevista", "—")
        valor = resultado.get("valor_mensal", contexto.get("valor_mensal", 0))

        notificacoes.enviar(
            usuario_id=contexto["inquilino_id"],
            tipo="contrato_confirmado",
            mensagem=(
                f"Contrato confirmado! Imóvel: '{titulo}'. "
                f"Aluguel mensal: R$ {valor:.2f}. Vigência até {fim}. "
                f"Atraso na desocupação gera multa diária de 1/30 do aluguel."
            ),
            imovel_id=contexto["imovel_id"],
        )

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        try:
            notificacoes = self.get_componente("notificacoes")
            notificacoes.enviar(
                usuario_id=contexto.get("inquilino_id", 0),
                tipo="atraso",
                mensagem=f"Não foi possível registrar o contrato: {str(erro)}",
                imovel_id=contexto.get("imovel_id"),
            )
        except Exception:
            pass

        return {"erro": True, "mensagem": str(erro), "tipo": type(erro).__name__}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="App 1 — Contrato com Notificação")
    parser.add_argument("--inquilino", type=int, default=1, help="ID do inquilino")
    parser.add_argument("--imovel",    type=int, required=True, help="ID do imóvel")
    args = parser.parse_args()

    print("=" * 60)
    print("APP 1 — Contrato de Aluguel com Notificação Automática")
    print("=" * 60)

    app = AppContrato()
    resultado = app.executar_operacao({
        "inquilino_id": args.inquilino,
        "imovel_id":    args.imovel,
    })

    print(f"\nResultado: {resultado}")
    print(f"\nLog de execução:")
    for entrada in app.get_log():
        print(f"  {entrada}")
