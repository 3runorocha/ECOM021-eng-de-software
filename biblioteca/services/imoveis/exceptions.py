class ImovelError(Exception):
    pass


class ImovelNaoEncontrado(ImovelError):
    def __init__(self, mensagem: str = "Imóvel não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(ImovelError):
    pass


class PermissaoNegada(ImovelError):
    def __init__(self, mensagem: str = "Sem permissão para esta operação"):
        super().__init__(mensagem)
