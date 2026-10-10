import os


SERVICES = {
    "imoveis":      {"url": os.getenv("IMOVEIS_URL",      "http://127.0.0.1:8001"), "porta": 8001, "descricao": "Portfolio de apartamentos e casas"},
    "usuarios":     {"url": os.getenv("USUARIOS_URL",     "http://127.0.0.1:8002"), "porta": 8002, "descricao": "Registro e autenticacao de usuarios"},
    "contratos":    {"url": os.getenv("CONTRATOS_URL",    "http://127.0.0.1:8003"), "porta": 8003, "descricao": "Locacao, encerramento e multa"},
    "notificacoes": {"url": os.getenv("NOTIFICACOES_URL", "http://127.0.0.1:8004"), "porta": 8004, "descricao": "Alertas de prazo e atraso"},
    "recomendacao": {"url": os.getenv("RECOMENDACAO_URL", "http://127.0.0.1:8005"), "porta": 8005, "descricao": "Recomendacao por perfil do usuario"},
    "agente":       {"url": os.getenv("AGENTE_URL",       "http://127.0.0.1:8006"), "porta": 8006, "descricao": "Busca conversacional sobre o portfolio"},
}

PUBLIC_ROUTES = {
    ("POST", "/usuarios/usuarios/registro"),
    ("POST", "/usuarios/usuarios/login"),
}

ROTAS_LIVRES = ["/health", "/services", "/docs", "/openapi.json", "/redoc"]


class ServiceRegistry:

    def __init__(self, services: dict):
        self._services = services

    def __contains__(self, nome: str) -> bool:
        return nome in self._services

    def url(self, nome: str) -> str:
        return self._services[nome]["url"]

    def itens(self):
        return self._services.items()