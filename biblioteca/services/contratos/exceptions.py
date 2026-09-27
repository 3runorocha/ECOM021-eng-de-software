class ContratoError(Exception):
    pass


class ContratoNaoEncontrado(ContratoError):
    def __init__(self, mensagem: str = "Contrato não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(ContratoError):
    pass


class ServicoIndisponivel(ContratoError):
    pass
