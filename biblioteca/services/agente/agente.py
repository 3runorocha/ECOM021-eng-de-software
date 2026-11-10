"""O agente: recebe pergunta em linguagem natural e responde usando as tools.

Quem fala com o modelo e o provedor escolhido em `provedores.py` (Gemini ou
Claude); aqui ficam so as instrucoes e as regras que valem para os dois.
"""
from ferramentas import FERRAMENTAS, chamador_atual
from exceptions import AgenteIndisponivel, RegraDeNegocio
from provedores import escolher_provedor

INSTRUCOES = """Você é o assistente de uma imobiliária que aluga apartamentos e
casas em Maceió, Recife e João Pessoa.

Responda SEMPRE em português do Brasil, de forma curta e direta.

Regras:
- Use as ferramentas para obter dados. Nunca invente imóvel, preço, endereço ou
  contrato: se não veio de uma ferramenta, você não sabe.
- Ao sugerir imóveis, cite o título, a cidade e o aluguel mensal de cada um.
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

        marca = chamador_atual.set(chamador)
        try:
            resultado = self._provedor.responder(INSTRUCOES, contexto, FERRAMENTAS)
        finally:
            chamador_atual.reset(marca)

        return {
            "resposta": resultado["resposta"] or "Não consegui formular uma resposta.",
            "ferramentas_usadas": resultado["ferramentas_usadas"],
            "modelo": self.modelo,
            "truncado": resultado["truncado"],
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
