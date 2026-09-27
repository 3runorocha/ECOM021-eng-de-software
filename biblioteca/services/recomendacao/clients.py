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


class ImovelClient:

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def buscar_imovel(self, imovel_id: int) -> dict | None:
        try:
            resp = httpx.get(
                f"{self._base_url}/imoveis/{imovel_id}", timeout=self._timeout
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Imóveis indisponível")

    def buscar_portfolio_completo(self) -> list[dict]:
        try:
            resp = httpx.get(f"{self._base_url}/imoveis/", timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Imóveis indisponível")