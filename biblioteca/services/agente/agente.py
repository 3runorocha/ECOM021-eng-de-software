"""O agente: recebe pergunta em linguagem natural e responde usando as tools.

Quem fala com o modelo e o provedor escolhido em `provedores.py` (Gemini ou
Claude); aqui ficam so as instrucoes e as regras que valem para os dois.
"""
from contingencia import descrever, extrair_filtros
from ferramentas import FERRAMENTAS, buscar_imoveis, chamador_atual, imoveis_encontrados
from exceptions import AgenteIndisponivel, ModeloLento, RegraDeNegocio
from provedores import escolher_provedor

INSTRUCOES = """Você é o assistente de uma imobiliária que aluga apartamentos e
casas em Maceió, Recife e João Pessoa.

Responda SEMPRE em português do Brasil, de forma curta e direta.

Regras:
- Use as ferramentas para obter dados. Nunca invente imóvel, preço, endereço ou
  contrato: se não veio de uma ferramenta, você não sabe.
- A tela mostra em cartões os imóveis que as ferramentas encontrarem. Na
  resposta, escreva no máximo três frases: diga quantos imóveis encontrou e
  destaque até três pelo título e pelo aluguel mensal.
- Escreva em texto simples, sem Markdown: nada de asteriscos, cerquilhas ou
  tabelas. Para listar, use uma linha por item começando com hífen.
- Se a busca não retornar nada, diga isso claramente e sugira afrouxar um
  critério (outra cidade, mais orçamento, menos quartos). Não ofereça imóvel que
  não apareceu no resultado.
- Se a pessoa não disser a cidade ou o orçamento, busque assim mesmo com o que
  ela deu, em vez de ficar perguntando.
- Você não registra, altera nem encerra contratos. Se pedirem isso, explique que
  a contratação é feita na tela de Contratos.
"""


INSTRUCOES_AVISO = """Você escreve avisos curtos de uma imobiliária para o
inquilino, em português do Brasil.

Regras:
- Use SOMENTE os fatos que vierem na mensagem. Não invente data, valor, endereço
  nem nome.
- NÃO faça contas. Não calcule multa, total devido, nem diferença de dias. Se um
  valor não foi informado, não mencione valor.
- Dois a quatro períodos, tom cordial e direto, sem saudação formal nem
  assinatura.
- Termine orientando a pessoa a procurar a imobiliária para renovar o contrato
  ou agendar a desocupação.
- Responda apenas com o texto do aviso, sem aspas e sem comentários.
"""


CAMPOS_DO_CARTAO = ("id", "titulo", "tipo", "cidade", "endereco", "quartos",
                    "banheiros", "area_m2", "valor_mensal")
MAX_CARTOES = 6


def resumir_imoveis(vistos: list) -> list:
    """Os imoveis que as ferramentas devolveram, sem repetir, para os cartoes."""
    unicos = {}
    for imovel in vistos:
        unicos.setdefault(imovel["id"], {c: imovel.get(c) for c in CAMPOS_DO_CARTAO})
    return list(unicos.values())[:MAX_CARTOES]


def resumo_padrao(usadas: list, encontrados: int) -> str:
    """Texto para quando o modelo nao escreveu a resposta dentro do prazo.

    Os cartoes continuam vindo da busca de verdade; so a frase e montada aqui.
    """
    if encontrados == 1:
        return "Encontrei 1 imóvel para a sua busca. Veja os detalhes abaixo."
    if encontrados:
        return f"Encontrei {encontrados} imóveis para a sua busca. Veja os detalhes abaixo."
    if any(u["ferramenta"] == "buscar_imoveis" for u in usadas):
        return ("Não encontrei imóveis com esses critérios. Tente outra cidade, "
                "um orçamento maior ou menos quartos.")
    return "Não consegui formular uma resposta a tempo. Tente de novo em alguns segundos."


class Agente:
    """Encapsula o provedor de modelo e as regras de quem pergunta.

    O provedor e escolhido ao criar o agente, mas a credencial so e exigida
    na hora da pergunta: o servico precisa subir e responder /health mesmo
    sem chave configurada.
    """

    def __init__(self, provedor=None):
        self._provedor = provedor or escolher_provedor()

    @property
    def provedor(self) -> str:
        return self._provedor.nome

    @property
    def modelo(self) -> str:
        return self._provedor.modelo

    def tem_credencial(self) -> bool:
        return self._provedor.disponivel()

    def perguntar(
        self, pergunta: str, inquilino_id: int = None, chamador: dict = None
    ) -> dict:
        texto = (pergunta or "").strip()
        if not texto:
            raise RegraDeNegocio("A pergunta não pode estar vazia")

        if chamador is not None:
            inquilino_id = chamador["id"]

        contexto = texto
        if inquilino_id is not None:
            contexto = (
                f"[inquilino_id do usuário autenticado: {inquilino_id}]" + chr(10) + texto
            )

        vistos = []
        marca = chamador_atual.set(chamador)
        marca_imoveis = imoveis_encontrados.set(vistos)
        try:
            try:
                resultado = self._provedor.responder(INSTRUCOES, contexto, FERRAMENTAS)
            except ModeloLento:
                resultado = self._contingencia(texto)
        finally:
            imoveis_encontrados.reset(marca_imoveis)
            chamador_atual.reset(marca)

        cartoes = resumir_imoveis(vistos)
        encontrados = len({i["id"] for i in vistos})
        resposta = resultado["resposta"] or resumo_padrao(resultado["ferramentas_usadas"], encontrados)
        if "contingencia" in resultado:
            resposta = (
                "O modelo não respondeu a tempo, então fiz uma busca direta "
                f"({descrever(resultado['contingencia'])}). {resposta}"
            )
        return {
            "resposta": resposta,
            "ferramentas_usadas": resultado["ferramentas_usadas"],
            "modelo": resultado.get("modelo", self.modelo),
            "truncado": resultado["truncado"],
            "imoveis": cartoes,
        }

    def _contingencia(self, pergunta: str) -> dict:
        """Busca direta com os filtros tirados da frase, sem modelo.

        Usa a mesma ferramenta do agente, entao os imoveis sao os de verdade e
        vao para os cartoes como numa resposta normal.
        """
        filtros = extrair_filtros(pergunta)
        buscar_imoveis(**filtros)
        return {
            "resposta": "",
            "ferramentas_usadas": [{"ferramenta": "buscar_imoveis", "argumentos": filtros}],
            "truncado": True,
            "modelo": "busca direta (contingência)",
            "contingencia": filtros,
        }

    def redigir_aviso(self, fatos: dict) -> str:
        """Redige o aviso de vencimento a partir de fatos já apurados.

        Sem ferramentas de propósito: quem levantou os contratos foi a aplicação,
        usando os componentes. O modelo só escreve o texto, não busca dados e
        não faz contas. Isso mantém a regra de multa num lugar só (o serviço de
        contratos) e tira do modelo a chance de inventar número.
        """
        if not fatos:
            raise RegraDeNegocio("Nenhum fato informado para o aviso")

        linhas = [f"- {chave}: {valor}" for chave, valor in fatos.items()]
        conteudo = "Fatos do contrato:" + chr(10) + chr(10).join(linhas)

        texto = self._provedor.redigir(INSTRUCOES_AVISO, conteudo)
        if not texto:
            raise AgenteIndisponivel("O modelo devolveu aviso vazio")
        return texto
