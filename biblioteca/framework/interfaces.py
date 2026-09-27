from abc import ABC, abstractmethod


class IComponente(ABC):

    @abstractmethod
    def inicializar(self) -> None:
        pass

    @abstractmethod
    def finalizar(self) -> None:
        pass

    @abstractmethod
    def get_nome(self) -> str:
        pass


class IComponenteImovel(IComponente):

    @abstractmethod
    def buscar_imoveis(self, filtros: dict) -> list[dict]:
        pass

    @abstractmethod
    def cadastrar_imovel(self, dados: dict) -> dict:
        pass

    @abstractmethod
    def definir_disponibilidade(self, imovel_id: int, disponivel: bool) -> None:
        pass


class IComponenteUsuario(IComponente):

    @abstractmethod
    def registrar(self, dados: dict) -> dict:
        pass

    @abstractmethod
    def autenticar(self, email: str, senha: str) -> dict | None:
        pass

    @abstractmethod
    def buscar_usuario(self, usuario_id: int) -> dict | None:
        pass


class IComponenteContrato(IComponente):

    @abstractmethod
    def registrar_contrato(self, inquilino_id: int, imovel_id: int) -> dict:
        pass

    @abstractmethod
    def encerrar_contrato(self, contrato_id: int) -> dict:
        pass

    @abstractmethod
    def listar_contratos(self, inquilino_id: int) -> list[dict]:
        pass


class IComponenteNotificacao(IComponente):

    @abstractmethod
    def enviar(self, usuario_id: int, tipo: str, mensagem: str, imovel_id: int = None) -> dict:
        pass

    @abstractmethod
    def listar(self, usuario_id: int) -> list[dict]:
        pass


class IComponenteRecomendacao(IComponente):

    @abstractmethod
    def recomendar(self, usuario_id: int, limite: int) -> list[dict]:
        pass

    @abstractmethod
    def obter_perfil(self, usuario_id: int) -> dict:
        pass