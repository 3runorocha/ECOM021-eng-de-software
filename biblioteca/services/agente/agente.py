"""O agente: recebe pergunta em linguagem natural e responde usando as tools."""
import os

import anthropic

from ferramentas import FERRAMENTAS
from exceptions import AgenteIndisponivel, RegraDeNegocio

MODELO = os.getenv("AGENTE_MODELO", "claude-opus-5-5")
MAX_TOKENS = 4096
# Extrair filtros de uma frase e resumir o resultado e tarefa simples; o default
# do Opus 5.5 e medium, e o skill recomenda deixar explicito.
ESFORCO = os.getenv("AGENTE_ESFORCO", "medium")
# Teto de voltas do loop, para uma pergunta ruim nao virar conta aberta.
MAX_ITERACOES = 8

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
    """Encapsula o cliente e o loop de ferramentas.

    O cliente e criado sob demanda: o servico precisa subir e responder
    /health mesmo sem credencial configurada, senao uma maquina sem chave
    derruba a composicao inteira.
    """

    def __init__(self):
        self._cliente = None

    SEM_CREDENCIAL = (
        "Nenhuma credencial da Anthropic encontrada. Defina ANTHROPIC_API_KEY "
        "no ambiente (ou rode `ant auth login`) e reinicie o serviço."
    )

    def _obter_cliente(self) -> anthropic.Anthropic:
        if self._cliente is None:
            # O construtor NAO falha sem credencial: o SDK so reclama ao montar
            # o header da requisicao, e com TypeError. Entao a checagem tem de
            # ser feita aqui, olhando as tres fontes que ele aceita.
            cliente = anthropic.Anthropic()
            if not (cliente.api_key or cliente.auth_token or cliente.credentials):
                raise AgenteIndisponivel(self.SEM_CREDENCIAL)
            self._cliente = cliente
        return self._cliente

    def tem_credencial(self) -> bool:
        try:
            self._obter_cliente()
            return True
        except AgenteIndisponivel:
            return False

    def perguntar(self, pergunta: str, inquilino_id: int = None) -> dict:
        texto = (pergunta or "").strip()
        if not texto:
            raise RegraDeNegocio("A pergunta não pode estar vazia")

        cliente = self._obter_cliente()

        contexto = texto
        if inquilino_id is not None:
            contexto = (
                f"[inquilino_id do usuário autenticado: {inquilino_id}]\n{texto}"
            )

        try:
            runner = cliente.beta.messages.tool_runner(
                model=MODELO,
                max_tokens=MAX_TOKENS,
                system=INSTRUCOES,
                output_config={"effort": ESFORCO},
                tools=FERRAMENTAS,
                messages=[{"role": "user", "content": contexto}],
            )

            ferramentas_usadas = []
            ultima = None
            iteracoes = 0
            for mensagem in runner:
                ultima = mensagem
                iteracoes += 1
                for bloco in mensagem.content:
                    if bloco.type == "tool_use":
                        ferramentas_usadas.append(
                            {"ferramenta": bloco.name, "argumentos": bloco.input}
                        )
                if iteracoes >= MAX_ITERACOES:
                    break
        except anthropic.APIStatusError as erro:
            raise AgenteIndisponivel(
                f"A API da Anthropic recusou a chamada ({erro.status_code}): {erro}"
            )
        except anthropic.APIConnectionError as erro:
            raise AgenteIndisponivel(f"Falha ao falar com a API da Anthropic: {erro}")
        except TypeError as erro:
            # O SDK levanta TypeError quando nao consegue resolver autenticacao.
            # Sem isto a falta de chave vira 500 em vez de 503.
            if "authentication" in str(erro).lower():
                raise AgenteIndisponivel(self.SEM_CREDENCIAL)
            raise

        if ultima is None:
            raise AgenteIndisponivel("O modelo não devolveu resposta")

        # stop_details so vem preenchido quando stop_reason == "refusal".
        if ultima.stop_reason == "refusal":
            motivo = getattr(ultima, "stop_details", None)
            raise RegraDeNegocio(
                "O modelo recusou responder a esta pergunta"
                + (f" ({motivo.category})" if motivo else "")
            )

        resposta = "".join(
            bloco.text for bloco in ultima.content if bloco.type == "text"
        ).strip()

        return {
            "resposta": resposta or "Não consegui formular uma resposta.",
            "ferramentas_usadas": ferramentas_usadas,
            "modelo": MODELO,
            "truncado": iteracoes >= MAX_ITERACOES
            and ultima.stop_reason == "tool_use",
        }

    def redigir_aviso(self, fatos: dict) -> str:
        """Redige o aviso de vencimento a partir de fatos já apurados.

        Sem ferramentas de propósito: quem levantou os contratos foi a aplicação,
        usando os componentes. O modelo só escreve o texto -- não busca dados e
        não faz contas. Isso mantém a regra de multa num lugar só (o serviço de
        contratos) e tira do modelo a chance de inventar número.
        """
        if not fatos:
            raise RegraDeNegocio("Nenhum fato informado para o aviso")

        cliente = self._obter_cliente()
        linhas = [f"- {chave}: {valor}" for chave, valor in fatos.items()]
        conteudo = "Fatos do contrato:" + chr(10) + chr(10).join(linhas)

        try:
            resposta = cliente.messages.create(
                model=MODELO,
                max_tokens=600,
                system=INSTRUCOES_AVISO,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": conteudo}],
            )
        except anthropic.APIStatusError as erro:
            raise AgenteIndisponivel(
                f"A API da Anthropic recusou a chamada ({erro.status_code}): {erro}"
            )
        except anthropic.APIConnectionError as erro:
            raise AgenteIndisponivel(f"Falha ao falar com a API da Anthropic: {erro}")
        except TypeError as erro:
            if "authentication" in str(erro).lower():
                raise AgenteIndisponivel(self.SEM_CREDENCIAL)
            raise

        if resposta.stop_reason == "refusal":
            raise RegraDeNegocio("O modelo recusou redigir este aviso")

        texto = "".join(
            bloco.text for bloco in resposta.content if bloco.type == "text"
        ).strip()
        if not texto:
            raise AgenteIndisponivel("O modelo devolveu aviso vazio")
        return texto
