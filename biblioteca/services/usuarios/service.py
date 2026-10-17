from models import UsuarioCreate, UsuarioLogin, UsuarioPublico, UsuarioUpdate
from repository import UsuarioRepository
from security import PasswordHasher, TokenService
from exceptions import (
    UsuarioNaoEncontrado, CredenciaisInvalidas, PermissaoNegada, TokenInvalido,
)

CAMPOS_SO_DE_ADMIN = {"tipo", "ativo"}


class UsuarioService:

    def __init__(
        self,
        repository: UsuarioRepository,
        hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self._repo = repository
        self._hasher = hasher
        self._tokens = token_service
        self._hash_falso = hasher.hash("senha-para-equalizar-tempo")

    def registrar(self, usuario: UsuarioCreate) -> UsuarioPublico:
        if usuario.tipo != "inquilino" and self._repo.existe_algum():
            raise PermissaoNegada(
                "Cadastro público cria só inquilino; proprietário e admin são "
                "definidos por um admin (só o primeiro usuário nasce admin)"
            )
        senha_hash = self._hasher.hash(usuario.senha)
        novo_id = self._repo.inserir(
            usuario.nome, usuario.email, senha_hash, usuario.tipo
        )
        return self._repo.buscar_por_id(novo_id)

    def login(self, credenciais: UsuarioLogin) -> dict:
        encontrado = self._repo.buscar_ativo_com_hash(credenciais.email)
        if encontrado is None:
            self._hasher.verificar(credenciais.senha, self._hash_falso)
            raise CredenciaisInvalidas()

        usuario, senha_hash = encontrado
        if not self._hasher.verificar(credenciais.senha, senha_hash):
            raise CredenciaisInvalidas()

        token = self._tokens.gerar(usuario.id, usuario.email)
        return {
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "tipo": usuario.tipo,
            },
        }

    def listar_usuarios(self) -> list[UsuarioPublico]:
        return self._repo.listar()

    def buscar_usuario(self, usuario_id: int) -> UsuarioPublico:
        usuario = self._repo.buscar_por_id(usuario_id)
        if usuario is None:
            raise UsuarioNaoEncontrado()
        return usuario

    def atualizar_usuario(
        self, authorization: str, usuario_id: int, dados: UsuarioUpdate
    ) -> UsuarioPublico:
        chamador = self.buscar_usuario(self.validar_token(authorization)["usuario_id"])

        atual = self._repo.buscar_por_id(usuario_id)
        if atual is None:
            raise UsuarioNaoEncontrado()

        e_admin = chamador.tipo == "admin"
        if chamador.id != usuario_id and not e_admin:
            raise PermissaoNegada("Só o próprio usuário ou um admin altera este cadastro")

        campos = dados.model_dump(exclude_none=True)
        if CAMPOS_SO_DE_ADMIN & campos.keys() and not e_admin:
            raise PermissaoNegada("Só admin altera tipo ou situação de um usuário")
        if not campos:
            return atual

        self._repo.atualizar(usuario_id, campos)
        return self._repo.buscar_por_id(usuario_id)

    def validar_token(self, authorization: str) -> dict:
        token = authorization.replace("Bearer ", "")
        payload = self._tokens.validar(token)
        usuario = self._repo.buscar_por_id(payload["usuario_id"])
        if usuario is None or not usuario.ativo:
            raise TokenInvalido()
        return {"valido": True, **payload, "tipo": usuario.tipo}
