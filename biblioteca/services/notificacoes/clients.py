import httpx

from exceptions import ServicoIndisponivel


class EmprestimoClient:

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def listar_emprestimos(self) -> list[dict]:
        try:
            resp = httpx.get(
                f"{self._base_url}/emprestimos/", timeout=self._timeout
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Empréstimos indisponível")