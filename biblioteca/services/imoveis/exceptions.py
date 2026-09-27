class ImovelError(Exception):
    pass


class ImovelNaoEncontrado(ImovelError):
    def __init__(self, mensagem: str = "Imóvel não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(ImovelError):
    pass
