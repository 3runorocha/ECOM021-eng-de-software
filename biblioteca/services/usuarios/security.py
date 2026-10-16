import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from exceptions import TokenInvalido


class PasswordHasher:

    ALGORITMO = "pbkdf2_sha256"
    ITERACOES = 600_000

    def hash(self, senha: str) -> str:
        sal = secrets.token_hex(16)
        derivada = self._derivar(senha, sal, self.ITERACOES)
        return f"{self.ALGORITMO}${self.ITERACOES}${sal}${derivada}"

    def verificar(self, senha: str, guardado: str) -> bool:
        try:
            algoritmo, iteracoes, sal, esperada = guardado.split("$")
            iteracoes = int(iteracoes)
        except (ValueError, AttributeError):
            return False
        if algoritmo != self.ALGORITMO:
            return False
        return hmac.compare_digest(self._derivar(senha, sal, iteracoes), esperada)

    @staticmethod
    def _derivar(senha: str, sal: str, iteracoes: int) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", senha.encode(), bytes.fromhex(sal), iteracoes
        ).hex()


class TokenService:

    def __init__(self, secret: str, horas_validade: int = 8):
        if not secret:
            raise ValueError("TokenService exige um segredo não vazio")
        self._secret = secret.encode()
        self._horas_validade = horas_validade

    @staticmethod
    def _agora() -> datetime:
        return datetime.now(timezone.utc)

    def _assinar(self, raw: str) -> str:
        return hmac.new(self._secret, raw.encode(), hashlib.sha256).hexdigest()

    def gerar(self, usuario_id: int, email: str) -> str:
        nonce = secrets.token_hex(16)
        expires = int(
            (self._agora() + timedelta(hours=self._horas_validade)).timestamp()
        )
        raw = f"{usuario_id}:{email}:{expires}:{nonce}"
        return f"{raw}:{self._assinar(raw)}"

    def validar(self, token: str) -> dict:
        try:
            usuario_id, email, expires, nonce, signature = token.split(":")
            raw = f"{usuario_id}:{email}:{expires}:{nonce}"
            if not hmac.compare_digest(signature, self._assinar(raw)):
                raise ValueError("Assinatura inválida")
            if int(expires) < int(self._agora().timestamp()):
                raise ValueError("Token expirado")
            return {"usuario_id": int(usuario_id), "email": email}
        except Exception:
            raise TokenInvalido()
