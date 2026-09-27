import httpx

from exceptions import RegraDeNegocio, ServicoIndisponivel


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

    def definir_disponibilidade(self, imovel_id: int, disponivel: bool) -> None:
        try:
            resp = httpx.patch(
                f"{self._base_url}/imoveis/{imovel_id}/disponibilidade",
                params={"disponivel": disponivel},
                timeout=self._timeout,
            )
            if resp.status_code == 400:
                raise RegraDeNegocio(resp.json().get("detail"))
            resp.raise_for_status()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Imóveis indisponível")
