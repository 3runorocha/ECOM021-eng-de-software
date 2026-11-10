"""Provedores de modelo do agente: Gemini (Google) e Claude (Anthropic).

Os dois expoem a mesma interface (`disponivel`, `responder` e `redigir`), entao
o agente nao sabe qual esta usando. A escolha vem de AGENTE_PROVEDOR
("gemini" ou "anthropic"); sem ela, vale o primeiro que tiver credencial no
ambiente, com o Gemini na frente, porque tem nivel gratuito.

Os SDKs sao importados so na hora do uso: o servico sobe e responde /health
mesmo sem nenhum deles configurado.
"""
import inspect
import os
import time

import httpx

try:
    import httpx2
except ImportError:
    httpx2 = None

from exceptions import AgenteIndisponivel, ModeloLento, RegraDeNegocio

MAX_ITERACOES = 8
ESFORCO = os.getenv("AGENTE_ESFORCO", "medium")

ERROS_DE_PRAZO = (httpx.TimeoutException,) + ((httpx2.TimeoutException,) if httpx2 else ())
ERROS_DE_REDE = (httpx.TransportError,) + ((httpx2.TransportError,) if httpx2 else ())

SEM_CREDENCIAL = (
    "Nenhuma credencial de modelo encontrada. Defina GEMINI_API_KEY (chave "
    "gratuita em aistudio.google.com) ou ANTHROPIC_API_KEY no ambiente e "
    "reinicie o serviço."
)


class ProvedorGemini:
    """Gemini pela API do Google AI Studio, com o laco de ferramentas conduzido aqui.

    O SDK sabe executar as ferramentas sozinho, mas cada ida e volta ganhava um
    prazo proprio e uma chamada lenta comia o tempo todo da pergunta. Aqui ha
    um relogio unico por pergunta, medido no nivel gratuito para caber em 10 s:
    - o principal e o modelo lite (1,2 s por chamada, contra 3,6 s do flash);
    - as novas tentativas do proprio SDK ficam desligadas: com o modelo
      sobrecarregado ele tentava 5 vezes e a pergunta levava quase um minuto;
    - cada chamada tem prazo curto; se estourar, ou se o modelo estiver
      sobrecarregado ou sem cota, a primeira chamada passa ao proximo modelo e
      o modelo com problema fica de fora por um minuto;
    - se o tempo acabar depois da busca, a resposta sai sem o texto do modelo,
      e o agente resume a partir dos imoveis encontrados.
    """

    nome = "gemini"
    RESERVAS_PADRAO = "gemini-3.6-flash,gemini-3.8-flash"
    ERROS_PASSAGEIROS = (429, 500, 503, 504)
    PAUSA = 60.0
    ORCAMENTO = 9.0
    PRAZO_CHAMADA = 4.5
    PRAZO_MINIMO = 1.5
    PRAZO_DO_SERVIDOR = 10
    _pausados: dict = {}

    def __init__(self):
        self.modelo = os.getenv("AGENTE_MODELO_GEMINI", "gemini-3.5-flash-lite")
        reservas = os.getenv("AGENTE_RESERVAS_GEMINI", self.RESERVAS_PADRAO)
        self.reservas = [m.strip() for m in reservas.split(",") if m.strip() and m.strip() != self.modelo]
        self._cliente = None

    def disponivel(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    def _obter_cliente(self):
        if not self.disponivel():
            raise AgenteIndisponivel(SEM_CREDENCIAL)
        if self._cliente is None:
            from google import genai
            from google.genai import types
            self._cliente = genai.Client(http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            ))
        return self._cliente

    def _ordem(self) -> list:
        """Os modelos na ordem de tentativa, deixando de fora os pausados.

        Se todos estiverem pausados, tenta todos assim mesmo: e melhor arriscar
        do que recusar a pergunta sem tentar.
        """
        agora = time.monotonic()
        todos = [self.modelo] + self.reservas
        return [m for m in todos if self._pausados.get(m, 0.0) <= agora] or todos

    def _config_para(self, modelo: str, config, segundos: float):
        """Modelos lite nao aceitam nivel de raciocinio; os demais vao em 'low',
        que e o que cabe no orcamento de tempo.

        O prazo curto vale so do lado de ca: o SDK repassaria o mesmo valor ao
        servidor, que recusa prazo menor que 10 s. O cabecalho com o prazo do
        servidor vai preenchido, e o SDK nao o sobrescreve.
        """
        from google.genai import types
        pensamento = None
        if "lite" not in modelo:
            pensamento = types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
        prazo = types.HttpOptions(timeout=int(segundos * 1000),
                                  headers={"X-Server-Timeout": str(self.PRAZO_DO_SERVIDOR)})
        return config.model_copy(update={"thinking_config": pensamento, "http_options": prazo})

    def _gerar(self, conteudo, config, limite: float, modelos: list, prazo_max: float = None) -> tuple:
        """Tenta os modelos dados, na ordem, ate um responder dentro do limite.
        Devolve a resposta e o modelo que respondeu.

        O prazo de cada tentativa e curto quando ainda ha outro modelo para
        tentar; sem alternativa, a tentativa usa todo o tempo que resta.
        """
        from google.genai import errors
        cliente = self._obter_cliente()
        motivo = "O modelo não respondeu a tempo"
        for modelo in modelos:
            restante = limite - time.monotonic()
            if restante < self.PRAZO_MINIMO:
                break
            try:
                resposta = cliente.models.generate_content(
                    model=modelo, contents=conteudo,
                    config=self._config_para(modelo, config, min(restante, prazo_max or restante)),
                )
                return resposta, modelo
            except errors.APIError as erro:
                if erro.code not in self.ERROS_PASSAGEIROS:
                    raise AgenteIndisponivel(
                        f"A API do Gemini recusou a chamada ({erro.code}): {erro.message}"
                    )
                self._pausados[modelo] = time.monotonic() + self.PAUSA
                motivo = f"A API do Gemini recusou a chamada ({erro.code}): {erro.message}"
            except ERROS_DE_PRAZO:
                self._pausados[modelo] = time.monotonic() + self.PAUSA
                motivo = "O modelo não respondeu a tempo"
            except ERROS_DE_REDE as erro:
                raise AgenteIndisponivel(f"Falha ao falar com a API do Gemini: {erro}")
        raise ModeloLento(motivo)

    @staticmethod
    def _executar(funcao, argumentos: dict) -> str:
        """Chama a ferramenta convertendo os numeros para o tipo da assinatura:
        o Gemini manda 2.0 onde a funcao espera o inteiro 2."""
        assinatura = inspect.signature(funcao)
        convertidos = {}
        for nome, valor in argumentos.items():
            parametro = assinatura.parameters.get(nome)
            if parametro is None:
                continue
            tipo = parametro.annotation
            convertidos[nome] = tipo(valor) if tipo in (int, float, str) and valor is not None else valor
        return funcao(**convertidos)

    def responder(self, instrucoes: str, texto: str, ferramentas: list) -> dict:
        from google.genai import types
        funcoes = {f.__name__: f for f in ferramentas}
        config = types.GenerateContentConfig(
            system_instruction=instrucoes,
            tools=ferramentas,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        historico = [types.Content(role="user", parts=[types.Part(text=texto)])]
        limite = time.monotonic() + self.ORCAMENTO
        usadas, modelo = [], None

        for _ in range(MAX_ITERACOES):
            modelos = [modelo] if modelo else self._ordem()
            prazo = self.PRAZO_CHAMADA if len(modelos) > 1 else None
            try:
                resposta, modelo = self._gerar(historico, config, limite, modelos, prazo)
            except AgenteIndisponivel:
                if not usadas:
                    raise
                return {"resposta": "", "ferramentas_usadas": usadas, "truncado": True, "modelo": modelo}

            feedback = resposta.prompt_feedback
            if feedback is not None and feedback.block_reason:
                raise RegraDeNegocio(
                    f"O modelo recusou responder a esta pergunta ({feedback.block_reason})"
                )

            chamadas = resposta.function_calls or []
            if not chamadas:
                return {"resposta": (resposta.text or "").strip(), "ferramentas_usadas": usadas,
                        "truncado": False, "modelo": modelo}

            historico.append(resposta.candidates[0].content)
            respostas = []
            for chamada in chamadas:
                argumentos = dict(chamada.args or {})
                usadas.append({"ferramenta": chamada.name, "argumentos": argumentos})
                funcao = funcoes.get(chamada.name)
                saida = self._executar(funcao, argumentos) if funcao else '{"erro": "ferramenta desconhecida"}'
                respostas.append(types.Part.from_function_response(name=chamada.name, response={"result": saida}))
            historico.append(types.Content(role="user", parts=respostas))

        return {"resposta": "", "ferramentas_usadas": usadas, "truncado": True, "modelo": modelo}

    def redigir(self, instrucoes: str, conteudo: str) -> str:
        from google.genai import types
        limite = time.monotonic() + self.ORCAMENTO
        resposta, _ = self._gerar(conteudo, types.GenerateContentConfig(system_instruction=instrucoes),
                                  limite, self._ordem(), self.PRAZO_CHAMADA)
        return (resposta.text or "").strip()


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
