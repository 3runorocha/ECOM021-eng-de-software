"""App 3 — Aviso de vencimento redigido pelo agente.

Esta é a aplicação que fecha o argumento do projeto: o agente não é um apêndice
pendurado ao lado do sistema, ele é mais um componente orquestrado pelo mesmo
Template Method que as outras apps usam.

Divisão de trabalho, de propósito:

- quem levanta os contratos é a APP, pelos componentes (dado é dado);
- quem escreve o texto é o AGENTE (prosa é prosa);
- quem envia a notificação é a APP, pelo componente de notificações.

O modelo não busca dados, não faz conta e não dispara efeito colateral. Se o
agente estiver sem credencial, a app cai num texto padrão e segue avisando --
o aviso é a função, o agente é o acabamento.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import (
    ComponenteContratoHTTP,
    ComponenteImovelHTTP,
    ComponenteAgenteHTTP,
    ComponenteNotificacaoHTTP,
)


class AppAvisoVencimento(FrameworkBiblioteca):

    DIAS_ALERTA_PADRAO = 30

    def configurar_componentes(self) -> None:
        self.registrar_componente("contratos",    ComponenteContratoHTTP())
        self.registrar_componente("imoveis",      ComponenteImovelHTTP())
        self.registrar_componente("agente",       ComponenteAgenteHTTP())
        self.registrar_componente("notificacoes", ComponenteNotificacaoHTTP())

    def get_campos_obrigatorios(self) -> list[str]:
        return []

    def pre_processar(self, contexto: dict) -> None:
        """Levanta os contratos que precisam de aviso. Determinístico."""
        dias_alerta = contexto.get("dias_alerta", self.DIAS_ALERTA_PADRAO)
        contratos = self.get_componente("contratos")
        imoveis = self.get_componente("imoveis")

        portfolio = {i["id"]: i for i in imoveis.buscar_imoveis({})}
        hoje = date.today()

        pendentes = []
        for contrato in contratos.listar_contratos():
            if contrato["status"] == "encerrado":
                continue

            prevista = date.fromisoformat(contrato["data_fim_prevista"])
            dias = (prevista - hoje).days
            if dias > dias_alerta:
                continue

            imovel = portfolio.get(contrato["imovel_id"], {})
            pendentes.append({
                "contrato_id": contrato["id"],
                "inquilino_id": contrato["inquilino_id"],
                "imovel_id": contrato["imovel_id"],
                "imovel": imovel.get("titulo", f"Imóvel {contrato['imovel_id']}"),
                "cidade": imovel.get("cidade", "—"),
                "data_fim_prevista": contrato["data_fim_prevista"],
                "dias": dias,
                "valor_mensal": contrato["valor_mensal"],
                "vencido": dias < 0,
            })

        contexto["pendentes"] = pendentes

    def executar_logica(self, contexto: dict) -> dict:
        """Pede ao agente o texto de cada aviso."""
        agente = self.get_componente("agente")
        avisos = []

        for p in contexto["pendentes"]:
            fatos = {
                "imóvel": p["imovel"],
                "cidade": p["cidade"],
                "aluguel mensal": f"R$ {p['valor_mensal']:.2f}",
                "data de término prevista": p["data_fim_prevista"],
                "situação": (
                    f"contrato venceu há {abs(p['dias'])} dia(s)" if p["vencido"]
                    else f"faltam {p['dias']} dia(s) para o término"
                ),
            }
            try:
                mensagem = agente.redigir_aviso(fatos)
                redigido_por = "agente"
            except Exception:
                # Agente fora do ar ou sem credencial: o aviso sai mesmo assim.
                mensagem = self._texto_padrao(p)
                redigido_por = "texto padrão"

            avisos.append({**p, "mensagem": mensagem, "redigido_por": redigido_por})

        return {"avisos": avisos, "total": len(avisos)}

    def pos_processar(self, contexto: dict, resultado: dict) -> None:
        """Envia. O efeito colateral é da app, nunca do modelo."""
        notificacoes = self.get_componente("notificacoes")
        enviados = 0

        for aviso in resultado["avisos"]:
            try:
                notificacoes.enviar(
                    usuario_id=aviso["inquilino_id"],
                    tipo="atraso" if aviso["vencido"] else "prazo_proximo",
                    mensagem=aviso["mensagem"],
                    imovel_id=aviso["imovel_id"],
                )
                enviados += 1
            except Exception as erro:
                aviso["erro_envio"] = str(erro)

        resultado["enviados"] = enviados

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        return {
            "erro": True,
            "mensagem": str(erro),
            "tipo": type(erro).__name__,
            "pendentes_encontrados": len(contexto.get("pendentes", [])),
        }

    @staticmethod
    def _texto_padrao(p: dict) -> str:
        if p["vencido"]:
            return (
                f"O contrato do imóvel '{p['imovel']}' venceu em "
                f"{p['data_fim_prevista']}, há {abs(p['dias'])} dia(s). "
                "Procure a imobiliária para renovar ou agendar a desocupação."
            )
        return (
            f"O contrato do imóvel '{p['imovel']}' termina em "
            f"{p['data_fim_prevista']}, em {p['dias']} dia(s). "
            "Procure a imobiliária para renovar ou agendar a desocupação."
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="App 3 — Aviso de vencimento redigido pelo agente"
    )
    parser.add_argument(
        "--dias", type=int, default=AppAvisoVencimento.DIAS_ALERTA_PADRAO,
        help="Avisa contratos que terminam em até N dias (vencidos entram sempre)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("APP 3 — Aviso de Vencimento (agente + framework)")
    print("=" * 60)

    app = AppAvisoVencimento()
    resultado = app.executar_operacao({"dias_alerta": args.dias})

    if resultado.get("erro"):
        print(f"\nFalhou: {resultado['mensagem']}")
    else:
        print(f"\n{resultado['total']} aviso(s), {resultado.get('enviados', 0)} enviado(s):\n")
        for aviso in resultado["avisos"]:
            marca = "VENCIDO" if aviso["vencido"] else f"faltam {aviso['dias']}d"
            print(f"  [{marca}] {aviso['imovel']} — inquilino {aviso['inquilino_id']}")
            print(f"    redigido por: {aviso['redigido_por']}")
            print(f"    {aviso['mensagem']}")
            if aviso.get("erro_envio"):
                print(f"    ! falha ao enviar: {aviso['erro_envio']}")
            print()

    print("Log de execução:")
    for entrada in app.get_log():
        print(f"  {entrada}")
