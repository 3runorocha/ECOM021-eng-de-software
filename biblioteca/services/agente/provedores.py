"""Provedores de modelo do agente: Gemini (Google) e Claude (Anthropic).

Os dois expoem a mesma interface (`disponivel`, `responder` e `redigir`), entao
o agente nao sabe qual esta usando. A escolha vem de AGENTE_PROVEDOR
("gemini" ou "anthropic"); sem ela, vale o primeiro que tiver credencial no
ambiente, com o Gemini na frente, porque tem nivel gratuito.

Os SDKs sao importados so na hora do uso: o servico sobe e responde /health
mesmo sem nenhum deles configurado.
"""
import os

import httpx

from exceptions import AgenteIndisponivel, RegraDeNegocio

MAX_ITERACOES = 8
ESFORCO = os.getenv("AGENTE_ESFORCO", "medium")

SEM_CREDENCIAL = (
    "Nenhuma credencial de modelo encontrada. Defina GEMINI_API_KEY (chave "
    "gratuita em aistudio.google.com) ou ANTHROPIC_API_KEY no ambiente e "
    "reinicie o serviço."
)


class ProvedorGemini:
    """Gemini pela API do Google AI Studio, com chamada automatica de funcoes.

    O SDK executa as ferramentas sozinho, na mesma thread, e devolve o
    historico das chamadas; e dele que sai a lista de ferramentas usadas.
    """

    nome = "gemini"

    def __init__(self):
        self.modelo = os.getenv("AGENTE_MODELO_GEMINI", "gemini-3.8-flash")
        self._cliente = None

    def disponivel(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    def _obter_cliente(self):
        if not self.disponivel():
            raise AgenteIndisponivel(SEM_CREDENCIAL)
        if self._cliente is None:
            from google import genai
            self._cliente = genai.Client()
        return self._cliente

    def _gerar(self, conteudo: str, config):
        from google.genai import errors
        try:
            return self._obter_cliente().models.generate_content(
                model=self.modelo, contents=conteudo, config=config
            )
        except errors.APIError as erro:
            raise AgenteIndisponivel(
                f"A API do Gemini recusou a chamada ({erro.code}): {erro.message}"
            )
        except httpx.TransportError as erro:
            raise AgenteIndisponivel(f"Falha ao falar com a API do Gemini: {erro}")

    def _pensamento(self, nivel: str):
        from google.genai import types
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel(nivel.upper()))

    def responder(self, instrucoes: str, texto: str, ferramentas: list) -> dict:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=instrucoes,
            tools=ferramentas,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=MAX_ITERACOES
            ),
            thinking_config=self._pensamento(ESFORCO),
        )
        resposta = self._gerar(texto, config)

        feedback = resposta.prompt_feedback
        if feedback is not None and feedback.block_reason:
            raise RegraDeNegocio(
                f"O modelo recusou responder a esta pergunta ({feedback.block_reason})"
            )

        usadas = []
        for conteudo in resposta.automatic_function_calling_history or []:
            for parte in conteudo.parts or []:
                if parte.function_call:
                    usadas.append({
                        "ferramenta": parte.function_call.name,
                        "argumentos": dict(parte.function_call.args or {}),
                    })

        return {
            "resposta": (resposta.text or "").strip(),
            "ferramentas_usadas": usadas,
            "truncado": bool(resposta.function_calls),
        }

    def redigir(self, instrucoes: str, conteudo: str) -> str:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=instrucoes, thinking_config=self._pensamento("low")
        )
        return (self._gerar(conteudo, config).text or "").strip()


class ProvedorAnthropic:
    """Claude pela API da Anthropic, com o Tool Runner do SDK."""

    nome = "anthropic"
    MAX_TOKENS = 4096

    def __init__(self):
        self.modelo = os.getenv("AGENTE_MODELO", "claude-opus-5-5")
        self._cliente = None

    def _obter_cliente(self):
        if self._cliente is None:
            import anthropic
            cliente = anthropic.Anthropic()
            if not (cliente.api_key or cliente.auth_token or cliente.credentials):
                raise AgenteIndisponivel(SEM_CREDENCIAL)
            self._cliente = cliente
        return self._cliente

    def disponivel(self) -> bool:
        try:
            self._obter_cliente()
            return True
        except (AgenteIndisponivel, ImportError):
            return False

    def _chamar(self, funcao):
        import anthropic
        try:
            return funcao()
        except anthropic.APIStatusError as erro:
            raise AgenteIndisponivel(
                f"A API da Anthropic recusou a chamada ({erro.status_code}): {erro}"
            )
        except anthropic.APIConnectionError as erro:
            raise AgenteIndisponivel(f"Falha ao falar com a API da Anthropic: {erro}")
        except TypeError as erro:
            if "authentication" in str(erro).lower():
                raise AgenteIndisponivel(SEM_CREDENCIAL)
            raise

    def responder(self, instrucoes: str, texto: str, ferramentas: list) -> dict:
        from anthropic import beta_tool
        cliente = self._obter_cliente()

        def executar():
            runner = cliente.beta.messages.tool_runner(
                model=self.modelo,
                max_tokens=self.MAX_TOKENS,
                system=instrucoes,
                output_config={"effort": ESFORCO},
                tools=[beta_tool(f) for f in ferramentas],
                messages=[{"role": "user", "content": texto}],
            )
            usadas, ultima, iteracoes = [], None, 0
            for mensagem in runner:
                ultima = mensagem
                iteracoes += 1
                for bloco in mensagem.content:
                    if bloco.type == "tool_use":
                        usadas.append({"ferramenta": bloco.name, "argumentos": bloco.input})
                if iteracoes >= MAX_ITERACOES:
                    break
            return usadas, ultima, iteracoes

        usadas, ultima, iteracoes = self._chamar(executar)
        if ultima is None:
            raise AgenteIndisponivel("O modelo não devolveu resposta")
        if ultima.stop_reason == "refusal":
            motivo = getattr(ultima, "stop_details", None)
            raise RegraDeNegocio(
                "O modelo recusou responder a esta pergunta"
                + (f" ({motivo.category})" if motivo else "")
            )
        return {
            "resposta": "".join(b.text for b in ultima.content if b.type == "text").strip(),
            "ferramentas_usadas": usadas,
            "truncado": iteracoes >= MAX_ITERACOES and ultima.stop_reason == "tool_use",
        }

    def redigir(self, instrucoes: str, conteudo: str) -> str:
        cliente = self._obter_cliente()
        resposta = self._chamar(lambda: cliente.messages.create(
            model=self.modelo,
            max_tokens=600,
            system=instrucoes,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": conteudo}],
        ))
        if resposta.stop_reason == "refusal":
            raise RegraDeNegocio("O modelo recusou redigir este aviso")
        return "".join(b.text for b in resposta.content if b.type == "text").strip()


PROVEDORES = {"gemini": ProvedorGemini, "anthropic": ProvedorAnthropic}


def escolher_provedor():
    """AGENTE_PROVEDOR manda; sem ele, o primeiro com credencial, Gemini antes."""
    escolhido = os.getenv("AGENTE_PROVEDOR", "").strip().lower()
    if escolhido:
        if escolhido not in PROVEDORES:
            raise ValueError(
                f"AGENTE_PROVEDOR={escolhido!r} não existe; use gemini ou anthropic"
            )
        return PROVEDORES[escolhido]()
    candidatos = [ProvedorGemini(), ProvedorAnthropic()]
    return next((p for p in candidatos if p.disponivel()), candidatos[0])
