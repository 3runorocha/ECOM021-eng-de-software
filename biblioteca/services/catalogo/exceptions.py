class CatalogoError(Exception):
    pass


class LivroNaoEncontrado(CatalogoError):
    def __init__(self, mensagem: str = "Livro não encontrado"):
        super().__init__(mensagem)


class RegraDeNegocio(CatalogoError):
    pass