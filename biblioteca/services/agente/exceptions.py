class AgenteError(Exception):
    pass


class AgenteIndisponivel(AgenteError):
    """Falta credencial, ou a API da Anthropic nao respondeu."""


class RegraDeNegocio(AgenteError):
    pass
