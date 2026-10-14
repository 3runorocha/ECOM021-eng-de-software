import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from exceptions import TokenInvalido


class PasswordHasher:

    def __init__(self, secret: str):
        self._secret = secret

    def hash(self, senha: str) -> str:
        return hashlib.sha256((senha + self._secret).encode()).hexdigest()


class TokenService:

    def __init__(self, secret: str, horas_validade: int = 8):
        self._secret = secret
        self._horas_validade = horas_validade

    def _assinar(self, raw: str) -> str:
        return hashlib.sha256((raw + self._secret).encode()).hexdigest()

    @staticmethod
    def _agora() -> datetime:
        # Tem de ser consciente de fuso: datetime.utcnow() devolve um datetime
        # ingenuo, e .timestamp() o interpreta como hora LOCAL. Aqui (UTC-3) o
        # token declarava 11h de validade quando o pretendido era 8 -- a
        # duracao efetiva saia certa porque os dois lados erravam igual, mas o
        # campo expires gravado no token mentia para quem o lesse de fora.
        return datetime.now(timezone.utc)

    def gerar(self, usuario_id: int, email: str) -> str:
        nonce = secrets.token_hex(16)
        expires = int(
            (self._agora() + timedelta(hours=self._horas_validade)).timestamp()
        )
        raw = f"{usuario_id}:{email}:{expires}:{nonce}"
        return f"{raw}:{self._assinar(raw)}"

    def validar(self, token: str) -> dict:
        try:
            parts = token.split(":")
            usuario_id, email, expires, nonce, signature = (
                parts[0], parts[1], parts[2], parts[3], parts[4]
            )
            raw = f"{usuario_id}:{email}:{expires}:{nonce}"
            if signature != self._assinar(raw):
                raise ValueError("Assinatura inválida")
            if int(expires) < int(self._agora().timestamp()):
                raise ValueError("Token expirado")
            return {"usuario_id": int(usuario_id), "email": email}
        except Exception:
            raise TokenInvalido()
