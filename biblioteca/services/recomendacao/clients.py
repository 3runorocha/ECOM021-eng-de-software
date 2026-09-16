import httpx

from exceptions import ServicoIndisponivel


class EmprestimoClient:

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def buscar_historico(self, usuario_id: int) -> list[dict]:
        try:
            resp = httpx.get(
                f"{self._base_url}/emprestimos/",
                params={"usuario_id": usuario_id},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Empréstimos indisponível")


class CatalogoClient:

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def buscar_livro(self, livro_id: int) -> dict | None:
        try:
            resp = httpx.get(
                f"{self._base_url}/livros/{livro_id}", timeout=self._timeout
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Catálogo indisponível")

    def buscar_catalogo_completo(self) -> list[dict]:
        try:
            resp = httpx.get(f"{self._base_url}/livros/", timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Catálogo indisponível")