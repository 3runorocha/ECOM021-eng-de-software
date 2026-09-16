class NotificacaoError(Exception):
    pass


class NotificacaoNaoEncontrada(NotificacaoError):
    def __init__(self, mensagem: str = "Notificação não encontrada"):
        super().__init__(mensagem)


class ServicoIndisponivel(NotificacaoError):
    pass