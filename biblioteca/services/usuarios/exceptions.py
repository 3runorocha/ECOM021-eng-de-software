class UsuarioError(Exception):
    pass


class UsuarioNaoEncontrado(UsuarioError):
    def __init__(self, mensagem: str = "Usuário não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(UsuarioError):
    pass


class CredenciaisInvalidas(UsuarioError):
    def __init__(self, mensagem: str = "Credenciais inválidas"):
        super().__init__(mensagem)


class TokenInvalido(UsuarioError):
    def __init__(self, mensagem: str = "Token inválido ou expirado"):
        super().__init__(mensagem)