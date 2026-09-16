import httpx

from exceptions import RegraDeNegocio, ServicoIndisponivel


class CatalogoClient:

    def __init__(self, base_url: str, timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def atualizar_disponibilidade(self, livro_id: int, delta: int) -> None:
        try:
            resp = httpx.patch(
                f"{self._base_url}/livros/{livro_id}/disponibilidade",
                params={"delta": delta},
                timeout=self._timeout,
            )
            if resp.status_code == 400:
                raise RegraDeNegocio(resp.json().get("detail"))
            resp.raise_for_status()
        except httpx.RequestError:
            raise ServicoIndisponivel("Serviço de Catálogo indisponível")