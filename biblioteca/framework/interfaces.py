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


class IComponenteCatalogo(IComponente):

    @abstractmethod
    def buscar_livros(self, filtros: dict) -> list[dict]:
        pass

    @abstractmethod
    def cadastrar_livro(self, dados: dict) -> dict:
        pass

    @abstractmethod
    def atualizar_disponibilidade(self, livro_id: int, delta: int) -> None:
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


class IComponenteEmprestimo(IComponente):

    @abstractmethod
    def realizar_emprestimo(self, usuario_id: int, livro_id: int) -> dict:
        pass

    @abstractmethod
    def realizar_devolucao(self, emprestimo_id: int) -> dict:
        pass

    @abstractmethod
    def listar_emprestimos(self, usuario_id: int) -> list[dict]:
        pass


class IComponenteNotificacao(IComponente):

    @abstractmethod
    def enviar(self, usuario_id: int, tipo: str, mensagem: str, livro_id: int = None) -> dict:
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