from models import UsuarioCreate, UsuarioLogin, UsuarioPublico, UsuarioUpdate
from repository import UsuarioRepository
from security import PasswordHasher, TokenService
from exceptions import UsuarioNaoEncontrado, CredenciaisInvalidas


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

    def registrar(self, usuario: UsuarioCreate) -> UsuarioPublico:
        senha_hash = self._hasher.hash(usuario.senha)
        novo_id = self._repo.inserir(
            usuario.nome, usuario.email, senha_hash, usuario.tipo
        )
        return self._repo.buscar_por_id(novo_id)

    def login(self, credenciais: UsuarioLogin) -> dict:
        senha_hash = self._hasher.hash(credenciais.senha)
        usuario = self._repo.buscar_por_credenciais(credenciais.email, senha_hash)
        if usuario is None:
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
        self, usuario_id: int, dados: UsuarioUpdate
    ) -> UsuarioPublico:
        atual = self._repo.buscar_por_id(usuario_id)
        if atual is None:
            raise UsuarioNaoEncontrado()

        campos = dados.model_dump(exclude_none=True)
        if not campos:
            return atual

        self._repo.atualizar(usuario_id, campos)
        return self._repo.buscar_por_id(usuario_id)

    def validar_token(self, authorization: str) -> dict:
        token = authorization.replace("Bearer ", "")
        payload = self._tokens.validar(token)
        return {"valido": True, **payload}
