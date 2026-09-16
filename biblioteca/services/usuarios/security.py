import hashlib
import secrets
from datetime import datetime, timedelta

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

    def gerar(self, usuario_id: int, email: str) -> str:
        nonce = secrets.token_hex(16)
        expires = int(
            (datetime.utcnow() + timedelta(hours=self._horas_validade)).timestamp()
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
            if int(expires) < int(datetime.utcnow().timestamp()):
                raise ValueError("Token expirado")
            return {"usuario_id": int(usuario_id), "email": email}
        except Exception:
            raise TokenInvalido()
