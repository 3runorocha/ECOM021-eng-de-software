class EmprestimoError(Exception):
    pass


class EmprestimoNaoEncontrado(EmprestimoError):
    def __init__(self, mensagem: str = "Empréstimo não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(EmprestimoError):
    pass


class ServicoIndisponivel(EmprestimoError):
    pass