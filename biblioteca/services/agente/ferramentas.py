"""Ferramentas do agente.

Este modulo e o argumento de arquitetura do projeto: o agente nao fala com os
microsservicos por conta propria, ele usa a MESMA camada de componentes que as
aplicacoes convencionais do framework (`framework/componentes.py`). Cada
ferramenta aqui e uma casca fina sobre um metodo de `IComponenteImovel` ou
`IComponenteContrato` -- a assinatura do componente ja e, na pratica, a
assinatura de uma tool.

As ferramentas sao todas de LEITURA. Registrar contrato e acao com efeito
colateral e dinheiro envolvido; isso nao fica a cargo do modelo nesta fase.

Sao funcoes Python comuns, sem depender de SDK: cada provedor de modelo
(`provedores.py`) converte a assinatura e a docstring para o formato da sua
API. Por isso as docstrings seguem o formato Args, que os dois entendem.
"""
import json
import os
import sys
from contextvars import ContextVar

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "framework")
)

from componentes import (
    ComponenteImovelHTTP,
    ComponenteContratoHTTP,
)

imoveis = ComponenteImovelHTTP()
contratos = ComponenteContratoHTTP()

chamador_atual: ContextVar = ContextVar("chamador_atual", default=None)
imoveis_encontrados: ContextVar = ContextVar("imoveis_encontrados", default=None)


def _anotar(lista: list) -> None:
    """Guarda os imoveis vistos pelas ferramentas, para a tela mostrar em cartoes.

    Vale para qualquer provedor: o SDK executa a ferramenta na mesma thread da
    pergunta, entao a lista aberta pelo agente e a que recebe os imoveis.
    """
    destino = imoveis_encontrados.get()
    if destino is not None:
        destino.extend(lista)


def _json(valor) -> str:
    """Resultado de tool precisa ser texto; JSON e o formato mais legivel."""
    return json.dumps(valor, ensure_ascii=False, default=str)


def buscar_imoveis(
    cidade: str = "",
    tipo: str = "",
    quartos_min: int = 0,
    valor_max: float = 0.0,
    valor_min: float = 0.0,
) -> str:
    """Busca imoveis DISPONIVEIS para aluguel no portfolio.

    Use esta ferramenta sempre que a pessoa descrever o que procura. Todos os
    filtros sao opcionais: envie apenas os que a pessoa mencionou. Um filtro
    omitido nao restringe a busca.

    Args:
        cidade: Nome da cidade, por exemplo "Maceio", "Recife", "Joao Pessoa".
        tipo: "apartamento" ou "casa". Deixe vazio se a pessoa nao disse.
        quartos_min: Numero minimo de quartos. 0 significa sem minimo.
        valor_max: Aluguel mensal maximo em reais. 0 significa sem teto.
        valor_min: Aluguel mensal minimo em reais. 0 significa sem piso.
    """
    filtros = {"disponivel": True}
    if cidade:
        filtros["cidade"] = cidade
    if tipo:
        filtros["tipo"] = tipo
    if quartos_min:
        filtros["quartos_min"] = quartos_min
    if valor_max:
        filtros["valor_max"] = valor_max
    if valor_min:
        filtros["valor_min"] = valor_min

    encontrados = imoveis.buscar_imoveis(filtros)
    _anotar(encontrados)
    return _json({"total": len(encontrados), "imoveis": encontrados})


def detalhar_imovel(imovel_id: int) -> str:
    """Devolve os dados completos de um imovel especifico pelo id.

    Use quando a pessoa perguntar sobre um imovel que ja apareceu na conversa.

    Args:
        imovel_id: Identificador do imovel.
    """
    portfolio = imoveis.buscar_imoveis({})
    imovel = next((i for i in portfolio if i["id"] == imovel_id), None)
    if imovel is None:
        return _json({"erro": f"Imovel {imovel_id} nao existe no portfolio"})
    _anotar([imovel])
    return _json(imovel)


def listar_contratos(inquilino_id: int) -> str:
    """Lista os contratos de aluguel de um inquilino, em vigor e encerrados.

    Use quando a pessoa perguntar sobre os proprios contratos, o que ja alugou,
    prazos ou multas.

    Args:
        inquilino_id: Identificador do inquilino.
    """
    chamador = chamador_atual.get()
    if chamador and chamador["tipo"] != "admin" and inquilino_id != chamador["id"]:
        return _json({"erro": "Sem permissão para ver contratos de outro inquilino"})
    return _json(contratos.listar_contratos(inquilino_id))


FERRAMENTAS = [buscar_imoveis, detalhar_imovel, listar_contratos]
