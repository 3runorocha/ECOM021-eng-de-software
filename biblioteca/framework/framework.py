from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from interfaces import IComponente


class FrameworkBiblioteca(ABC):

    def __init__(self):
        self._componentes: dict[str, IComponente] = {}
        self._log: list[dict]                     = []
        self._inicializado: bool                  = False

    def executar_operacao(self, contexto: dict = None) -> Any:
        if contexto is None:
            contexto = {}

        resultado = None
        inicio = datetime.now()

        try:
            self._inicializar_componentes()
            self._validar_pre_condicoes(contexto)
            self.pre_processar(contexto)
            resultado = self.executar_logica(contexto)
            self.pos_processar(contexto, resultado)

        except Exception as erro:
            resultado = self.tratar_erro(contexto, erro)

        finally:
            duracao = (datetime.now() - inicio).total_seconds()
            self._registrar_log(contexto, resultado, duracao)
            self._finalizar_componentes()

        return resultado

    def _inicializar_componentes(self) -> None:
        if not self._inicializado:
            self.configurar_componentes()
            self._inicializado = True

        for nome, componente in self._componentes.items():
            componente.inicializar()

    def _validar_pre_condicoes(self, contexto: dict) -> None:
        campos_obrigatorios = self.get_campos_obrigatorios()
        for campo in campos_obrigatorios:
            if campo not in contexto:
                raise ValueError(
                    f"Campo obrigatório ausente no contexto: '{campo}'. "
                    f"Campos exigidos: {campos_obrigatorios}"
                )

    def _registrar_log(self, contexto: dict, resultado: Any, duracao: float) -> None:
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "operacao": self.__class__.__name__,
            "duracao_segundos": round(duracao, 4),
            "contexto_resumo": {k: v for k, v in contexto.items() if k != "senha"},
            "status": "erro" if isinstance(resultado, dict) and resultado.get("erro") else "ok",
        }
        self._log.append(entrada)

    def _finalizar_componentes(self) -> None:
        for componente in self._componentes.values():
            try:
                componente.finalizar()
            except Exception:
                pass

    def registrar_componente(self, nome: str, componente: IComponente) -> None:
        self._componentes[nome] = componente

    def get_componente(self, nome: str) -> IComponente:
        if nome not in self._componentes:
            raise KeyError(
                f"Componente '{nome}' não registrado. "
                f"Registre-o em configurar_componentes() via registrar_componente()."
            )
        return self._componentes[nome]

    def get_log(self) -> list[dict]:
        return self._log

    @abstractmethod
    def configurar_componentes(self) -> None:
        pass

    @abstractmethod
    def executar_logica(self, contexto: dict) -> Any:
        pass

    def configurar_componentes(self) -> None:
        pass

    def pre_processar(self, contexto: dict) -> None:
        pass

    def pos_processar(self, contexto: dict, resultado: Any) -> None:
        pass

    def tratar_erro(self, contexto: dict, erro: Exception) -> dict:
        return {"erro": True, "mensagem": str(erro), "tipo": type(erro).__name__}

    def get_campos_obrigatorios(self) -> list[str]:
        return []