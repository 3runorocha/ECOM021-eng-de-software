class GatewayError(Exception):
    status_code = 500

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ServicoNaoEncontrado(GatewayError):
    status_code = 404


class TokenInvalido(GatewayError):
    status_code = 401


class ServicoIndisponivel(GatewayError):
    status_code = 502