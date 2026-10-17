from models import Imovel, ImovelCreate, ImovelUpdate
from repository import ImovelRepository
from exceptions import ImovelNaoEncontrado, PermissaoNegada, RegraDeNegocio

PODEM_ADMINISTRAR_PORTFOLIO = {"admin", "proprietario"}


def exigir(chamador: dict | None, permitidos: set, acao: str) -> None:
    if chamador is not None and chamador["tipo"] not in permitidos:
        raise PermissaoNegada(f"Seu perfil não pode {acao}")


class ImovelService:

    def __init__(self, repository: ImovelRepository):
        self._repo = repository

    def listar_imoveis(
        self,
        cidade: str = None,
        tipo: str = None,
        quartos_min: int = None,
        valor_min: float = None,
        valor_max: float = None,
        disponivel: bool = None,
    ) -> list[Imovel]:
        if valor_min is not None and valor_max is not None and valor_min > valor_max:
            raise RegraDeNegocio("valor_min não pode ser maior que valor_max")
        return self._repo.listar(
            cidade=cidade, tipo=tipo, quartos_min=quartos_min,
            valor_min=valor_min, valor_max=valor_max, disponivel=disponivel,
        )

    def buscar_imovel(self, imovel_id: int) -> Imovel:
        imovel = self._repo.buscar_por_id(imovel_id)
        if imovel is None:
            raise ImovelNaoEncontrado()
        return imovel

    def cadastrar_imovel(
        self, dados: ImovelCreate, chamador: dict | None = None
    ) -> Imovel:
        exigir(chamador, PODEM_ADMINISTRAR_PORTFOLIO, "cadastrar imóvel")
        novo_id = self._repo.inserir(dados)
        return self._repo.buscar_por_id(novo_id)

    def atualizar_imovel(
        self, imovel_id: int, dados: ImovelUpdate, chamador: dict | None = None
    ) -> Imovel:
        exigir(chamador, PODEM_ADMINISTRAR_PORTFOLIO, "alterar imóvel")
        atual = self._repo.buscar_por_id(imovel_id)
        if atual is None:
            raise ImovelNaoEncontrado()

        campos = dados.model_dump(exclude_none=True)
        if not campos:
            return atual

        self._repo.atualizar(imovel_id, campos)
        return self._repo.buscar_por_id(imovel_id)

    def remover_imovel(self, imovel_id: int, chamador: dict | None = None) -> None:
        exigir(chamador, PODEM_ADMINISTRAR_PORTFOLIO, "remover imóvel")
        atual = self._repo.buscar_por_id(imovel_id)
        if atual is None:
            raise ImovelNaoEncontrado()
        if not atual.disponivel:
            raise RegraDeNegocio(
                f"Imóvel '{atual.titulo}' está alugado; encerre o contrato antes de remover"
            )
        self._repo.remover(imovel_id)

    def definir_disponibilidade(
        self, imovel_id: int, disponivel: bool, chamador: dict | None = None
    ) -> dict:
        """Substitui o antigo atualizar_disponibilidade(delta).

        Um imovel nao tem N exemplares: ou esta livre, ou esta alugado. Exigir
        que o estado mude de fato preserva a guarda que o acervo tinha ("nenhum
        exemplar disponivel") e da ao servico de contratos um 400 para tratar
        quando duas locacoes disputam o mesmo imovel.
        """
        exigir(chamador, {"admin"}, "mudar a disponibilidade à mão")
        imovel = self._repo.buscar_por_id(imovel_id)
        if imovel is None:
            raise ImovelNaoEncontrado()

        if imovel.disponivel == disponivel:
            estado = "disponível" if disponivel else "indisponível"
            raise RegraDeNegocio(f"Imóvel '{imovel.titulo}' já está {estado}")

        self._repo.atualizar(imovel_id, {"disponivel": int(disponivel)})
        return {"imovel_id": imovel_id, "disponivel": disponivel}
