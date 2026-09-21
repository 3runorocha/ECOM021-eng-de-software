import os


SERVICES = {
    "catalogo":     {"url": os.getenv("CATALOGO_URL",     "http://localhost:8001"), "porta": 8001, "descricao": "Gerenciamento do acervo de livros"},
    "usuarios":     {"url": os.getenv("USUARIOS_URL",     "http://localhost:8002"), "porta": 8002, "descricao": "Registro e autenticacao de usuarios"},
    "emprestimos":  {"url": os.getenv("EMPRESTIMOS_URL",  "http://localhost:8003"), "porta": 8003, "descricao": "Controle de emprestimos e devolucoes"},
    "notificacoes": {"url": os.getenv("NOTIFICACOES_URL", "http://localhost:8004"), "porta": 8004, "descricao": "Alertas de prazo e atraso"},
    "recomendacao": {"url": os.getenv("RECOMENDACAO_URL", "http://localhost:8005"), "porta": 8005, "descricao": "Recomendacao por perfil do usuario"},
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