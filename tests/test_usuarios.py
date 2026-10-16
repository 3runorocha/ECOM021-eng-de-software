"""Serviço de usuários: login e as regras de quem pode virar ou mexer em quem."""
import pytest

from conftest import carregar

modelos, servico_mod, seguranca, excecoes = carregar(
    "usuarios", "models", "service", "security", "exceptions"
)

UsuarioCreate = modelos.UsuarioCreate
UsuarioLogin = modelos.UsuarioLogin
UsuarioPublico = modelos.UsuarioPublico
UsuarioUpdate = modelos.UsuarioUpdate
UsuarioService = servico_mod.UsuarioService
PasswordHasher = seguranca.PasswordHasher
TokenService = seguranca.TokenService
PermissaoNegada = excecoes.PermissaoNegada
CredenciaisInvalidas = excecoes.CredenciaisInvalidas
TokenInvalido = excecoes.TokenInvalido


class RepoFake:
    def __init__(self):
        self.linhas = {}

    def existe_algum(self):
        return bool(self.linhas)

    def inserir(self, nome, email, senha_hash, tipo):
        novo_id = len(self.linhas) + 1
        self.linhas[novo_id] = {
            "id": novo_id, "nome": nome, "email": email,
            "senha_hash": senha_hash, "tipo": tipo, "ativo": True,
        }
        return novo_id

    def _publico(self, linha):
        return UsuarioPublico(**{k: v for k, v in linha.items() if k != "senha_hash"})

    def buscar_por_id(self, usuario_id):
        linha = self.linhas.get(usuario_id)
        return self._publico(linha) if linha else None

    def buscar_ativo_com_hash(self, email):
        for linha in self.linhas.values():
            if linha["email"] == email and linha["ativo"]:
                return self._publico(linha), linha["senha_hash"]
        return None

    def listar(self):
        return [self._publico(l) for l in self.linhas.values()]

    def atualizar(self, usuario_id, campos):
        self.linhas[usuario_id].update(campos)


@pytest.fixture
def tokens():
    return TokenService("segredo-de-teste")


@pytest.fixture
def service(tokens):
    return UsuarioService(RepoFake(), PasswordHasher(), tokens)


def cadastrar(service, email, tipo="inquilino"):
    return service.registrar(UsuarioCreate(
        nome=email.split("@")[0], email=email, senha="senha123", tipo=tipo,
    ))


def token_de(service, email):
    return service.login(UsuarioLogin(email=email, senha="senha123"))["token"]


def test_primeiro_usuario_pode_ser_admin(service):
    """Bootstrap: sem isso não haveria como criar o primeiro administrador."""
    assert cadastrar(service, "admin@alugue.br", tipo="admin").tipo == "admin"


def test_cadastro_publico_nao_cria_segundo_admin(service):
    cadastrar(service, "admin@alugue.br", tipo="admin")
    with pytest.raises(PermissaoNegada):
        cadastrar(service, "intruso@alugue.br", tipo="admin")


def test_inquilino_e_proprietario_se_cadastram_livremente(service):
    cadastrar(service, "admin@alugue.br", tipo="admin")
    assert cadastrar(service, "ana@alugue.br").tipo == "inquilino"
    assert cadastrar(service, "bia@alugue.br", tipo="proprietario").tipo == "proprietario"


def test_tipo_fora_da_lista_e_recusado_pelo_modelo():
    with pytest.raises(ValueError):
        UsuarioCreate(nome="x", email="x@y.z", senha="s", tipo="superusuario")


def test_login_com_senha_certa_devolve_token(service, tokens):
    cadastrar(service, "ana@alugue.br")
    resposta = service.login(UsuarioLogin(email="ana@alugue.br", senha="senha123"))
    assert tokens.validar(resposta["token"])["email"] == "ana@alugue.br"
    assert "senha_hash" not in resposta["usuario"]


def test_login_com_senha_errada_e_recusado(service):
    cadastrar(service, "ana@alugue.br")
    with pytest.raises(CredenciaisInvalidas):
        service.login(UsuarioLogin(email="ana@alugue.br", senha="errada"))


def test_login_de_usuario_inexistente_e_recusado(service):
    with pytest.raises(CredenciaisInvalidas):
        service.login(UsuarioLogin(email="ninguem@alugue.br", senha="senha123"))


def test_usuario_altera_o_proprio_nome(service):
    ana = cadastrar(service, "ana@alugue.br")
    alterado = service.atualizar_usuario(
        token_de(service, "ana@alugue.br"), ana.id, UsuarioUpdate(nome="Ana Souza")
    )
    assert alterado.nome == "Ana Souza"


def test_usuario_nao_altera_outro_usuario(service):
    """Antes, qualquer usuário logado podia desativar o admin e bloquear o
    login dele."""
    admin = cadastrar(service, "admin@alugue.br", tipo="admin")
    cadastrar(service, "ana@alugue.br")
    with pytest.raises(PermissaoNegada):
        service.atualizar_usuario(
            token_de(service, "ana@alugue.br"), admin.id, UsuarioUpdate(ativo=False)
        )


def test_usuario_nao_se_promove_a_admin(service):
    cadastrar(service, "admin@alugue.br", tipo="admin")
    ana = cadastrar(service, "ana@alugue.br")
    with pytest.raises(PermissaoNegada):
        service.atualizar_usuario(
            token_de(service, "ana@alugue.br"), ana.id, UsuarioUpdate(tipo="admin")
        )


def test_usuario_nao_se_reativa_sozinho(service):
    cadastrar(service, "admin@alugue.br", tipo="admin")
    ana = cadastrar(service, "ana@alugue.br")
    with pytest.raises(PermissaoNegada):
        service.atualizar_usuario(
            token_de(service, "ana@alugue.br"), ana.id, UsuarioUpdate(ativo=True)
        )


def test_admin_altera_tipo_e_situacao_de_outro(service):
    cadastrar(service, "admin@alugue.br", tipo="admin")
    ana = cadastrar(service, "ana@alugue.br")
    alterado = service.atualizar_usuario(
        token_de(service, "admin@alugue.br"), ana.id,
        UsuarioUpdate(tipo="proprietario", ativo=False),
    )
    assert alterado.tipo == "proprietario"
    assert alterado.ativo is False


def test_alterar_sem_token_valido_e_recusado(service):
    ana = cadastrar(service, "ana@alugue.br")
    with pytest.raises(TokenInvalido):
        service.atualizar_usuario("token-falso", ana.id, UsuarioUpdate(nome="x"))


def test_token_assinado_com_o_segredo_antigo_nao_vale(service):
    """O segredo antigo estava no repositório; com ele dava para forjar token.
    Um token assinado com ele não pode mais passar."""
    cadastrar(service, "admin@alugue.br", tipo="admin")
    forjado = TokenService("biblioteca_secret_2025").gerar(1, "admin@alugue.br")
    with pytest.raises(TokenInvalido):
        service.validar_token(forjado)
