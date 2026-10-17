"""Serviço de imóveis: a regra de disponibilidade e os filtros."""
import pytest

from conftest import carregar

modelos, servico_mod, excecoes = carregar(
    "imoveis", "models", "service", "exceptions"
)

Imovel = modelos.Imovel
ImovelCreate = modelos.ImovelCreate
ImovelUpdate = modelos.ImovelUpdate
ImovelService = servico_mod.ImovelService
ImovelNaoEncontrado = excecoes.ImovelNaoEncontrado
RegraDeNegocio = excecoes.RegraDeNegocio
PermissaoNegada = excecoes.PermissaoNegada


def imovel(id=1, titulo="Casa no Farol", disponivel=True, valor=3100.0,
           cidade="Maceio", tipo="casa", quartos=3):
    return Imovel(
        id=id, titulo=titulo, tipo=tipo, endereco="Rua X, 1", cidade=cidade,
        quartos=quartos, banheiros=2, area_m2=120.0, valor_mensal=valor,
        disponivel=disponivel,
    )


class RepoFake:
    def __init__(self, imoveis=None):
        self.imoveis = {i.id: i for i in (imoveis or [])}
        self.filtros_recebidos = None

    def buscar_por_id(self, imovel_id):
        return self.imoveis.get(imovel_id)

    def listar(self, **filtros):
        self.filtros_recebidos = filtros
        return list(self.imoveis.values())

    def inserir(self, dados, disponivel=True):
        novo = Imovel(id=99, disponivel=disponivel, **dados.model_dump())
        self.imoveis[99] = novo
        return 99

    def atualizar(self, imovel_id, campos):
        atual = self.imoveis[imovel_id]
        campos = dict(campos)
        if "disponivel" in campos:
            campos["disponivel"] = bool(campos["disponivel"])
        self.imoveis[imovel_id] = atual.model_copy(update=campos)

    def remover(self, imovel_id):
        del self.imoveis[imovel_id]


@pytest.fixture
def repo():
    return RepoFake([imovel()])


@pytest.fixture
def service(repo):
    return ImovelService(repo)


def test_imovel_novo_nasce_disponivel(service):
    criado = service.cadastrar_imovel(ImovelCreate(
        titulo="Novo", tipo="apartamento", endereco="Rua Y, 2",
        cidade="Recife", quartos=2, banheiros=1, area_m2=60.0,
        valor_mensal=1800.0,
    ))
    assert criado.disponivel is True


def test_alugar_marca_indisponivel(service, repo):
    resultado = service.definir_disponibilidade(1, False)
    assert resultado == {"imovel_id": 1, "disponivel": False}
    assert repo.imoveis[1].disponivel is False


def test_alugar_imovel_ja_alugado_e_recusado(service):
    """A guarda que o acervo tinha ('nenhum exemplar disponível'), em booleano.

    É o que dá ao serviço de contratos um 400 para tratar quando duas locações
    disputam o mesmo imóvel.
    """
    service.definir_disponibilidade(1, False)
    with pytest.raises(RegraDeNegocio) as erro:
        service.definir_disponibilidade(1, False)
    assert "já está indisponível" in str(erro.value)


def test_liberar_imovel_ja_livre_e_recusado(service):
    with pytest.raises(RegraDeNegocio):
        service.definir_disponibilidade(1, True)


def test_disponibilidade_de_imovel_inexistente(service):
    with pytest.raises(ImovelNaoEncontrado):
        service.definir_disponibilidade(404, False)


def test_buscar_imovel_inexistente(service):
    with pytest.raises(ImovelNaoEncontrado):
        service.buscar_imovel(404)


def test_faixa_de_valor_invertida_e_recusada(service):
    with pytest.raises(RegraDeNegocio) as erro:
        service.listar_imoveis(valor_min=5000, valor_max=100)
    assert "valor_min" in str(erro.value)


def test_filtros_chegam_ao_repositorio(service, repo):
    service.listar_imoveis(cidade="Recife", tipo="casa", quartos_min=3,
                           valor_max=5000, disponivel=True)
    assert repo.filtros_recebidos == {
        "cidade": "Recife", "tipo": "casa", "quartos_min": 3,
        "valor_min": None, "valor_max": 5000, "disponivel": True,
    }


def test_atualizar_sem_campos_nao_toca_no_repositorio(service, repo):
    modelos_update = carregar("imoveis", "models").ImovelUpdate
    antes = repo.imoveis[1]
    depois = service.atualizar_imovel(1, modelos_update())
    assert depois == antes


def _repositorio_real(tmp_path):
    db_mod, repo_mod, mod = carregar("imoveis", "database", "repository", "models")
    database = db_mod.Database(str(tmp_path / "imoveis.db"))
    database.init_schema()
    repo = repo_mod.ImovelRepository(database)
    for titulo, cidade in [
        ("Apto Ponta Verde", "Maceio"),
        ("Casa Farol", "Maceió"),
        ("Apto Manaira", "Joao Pessoa"),
        ("Casa Bessa", "João Pessoa"),
        ("Studio Casa Forte", "Recife"),
    ]:
        repo.inserir(mod.ImovelCreate(
            titulo=titulo, tipo="casa", endereco="Rua X, 1", cidade=cidade,
            quartos=2, banheiros=1, area_m2=60.0, valor_mensal=1500.0,
        ))
    return repo


@pytest.mark.parametrize("busca", ["Maceió", "Maceio", "maceio", "MACEIÓ", "Macei"])
def test_filtro_de_cidade_ignora_acento_e_caixa(tmp_path, busca):
    """O seed grava 'Maceio' e o prompt do agente e o usuário escrevem 'Maceió';
    com LIKE puro, 'Maceió' não achava nada."""
    titulos = {i.titulo for i in _repositorio_real(tmp_path).listar(cidade=busca)}
    assert titulos == {"Apto Ponta Verde", "Casa Farol"}


def test_filtro_acha_joao_pessoa_com_e_sem_til(tmp_path):
    repo = _repositorio_real(tmp_path)
    com_til = {i.titulo for i in repo.listar(cidade="João Pessoa")}
    sem_til = {i.titulo for i in repo.listar(cidade="Joao Pessoa")}
    assert com_til == sem_til == {"Apto Manaira", "Casa Bessa"}


def test_filtro_de_cidade_nao_vaza_para_outras_cidades(tmp_path):
    assert [i.cidade for i in _repositorio_real(tmp_path).listar(cidade="Recife")] == ["Recife"]


INQUILINO = {"id": 7, "tipo": "inquilino"}
PROPRIETARIO = {"id": 8, "tipo": "proprietario"}
ADMIN = {"id": 1, "tipo": "admin"}

NOVO = dict(
    titulo="Novo", tipo="apartamento", endereco="Rua Y, 2", cidade="Recife",
    quartos=2, banheiros=1, area_m2=60.0, valor_mensal=1800.0,
)


def test_inquilino_nao_mexe_no_portfolio(service, repo):
    with pytest.raises(PermissaoNegada):
        service.cadastrar_imovel(ImovelCreate(**NOVO), INQUILINO)
    with pytest.raises(PermissaoNegada):
        service.atualizar_imovel(1, ImovelUpdate(valor_mensal=1.0), INQUILINO)
    with pytest.raises(PermissaoNegada):
        service.remover_imovel(1, INQUILINO)
    assert repo.imoveis[1].valor_mensal == 3100.0


def test_proprietario_administra_o_portfolio(service, repo):
    service.cadastrar_imovel(ImovelCreate(**NOVO), PROPRIETARIO)
    service.atualizar_imovel(1, ImovelUpdate(valor_mensal=2900.0), PROPRIETARIO)
    assert repo.imoveis[1].valor_mensal == 2900.0
    service.remover_imovel(1, PROPRIETARIO)
    assert 1 not in repo.imoveis


def test_disponibilidade_a_mao_so_admin(service):
    for chamador in (INQUILINO, PROPRIETARIO):
        with pytest.raises(PermissaoNegada):
            service.definir_disponibilidade(1, False, chamador)
    assert service.definir_disponibilidade(1, False, ADMIN)["disponivel"] is False


def test_chamada_interna_nao_e_restrita(service):
    """Sem identidade é o serviço de contratos ocupando ou liberando o imóvel."""
    assert service.definir_disponibilidade(1, False)["disponivel"] is False


def test_nao_remove_imovel_alugado(repo):
    repo.imoveis[1] = imovel(disponivel=False)
    with pytest.raises(RegraDeNegocio, match="alugado"):
        ImovelService(repo).remover_imovel(1, ADMIN)
    assert 1 in repo.imoveis
