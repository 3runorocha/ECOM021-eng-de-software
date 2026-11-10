class AgenteError(Exception):
    pass


class AgenteIndisponivel(AgenteError):
    """Falta credencial, ou a API do modelo (Gemini ou Anthropic) nao respondeu."""


class ModeloLento(AgenteIndisponivel):
    """O modelo existe e ha credencial, mas nao respondeu dentro do prazo."""


class RegraDeNegocio(AgenteError):
    pass
