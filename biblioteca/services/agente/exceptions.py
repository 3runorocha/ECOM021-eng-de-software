class AgenteError(Exception):
    pass


class AgenteIndisponivel(AgenteError):
    """Falta credencial, ou a API do modelo (Gemini ou Anthropic) nao respondeu."""


class RegraDeNegocio(AgenteError):
    pass
