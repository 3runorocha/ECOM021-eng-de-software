import secrets
import sqlite3


class Database:

    def __init__(self, db_path: str):
        self._db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        conn = self.connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome        TEXT    NOT NULL,
                    email       TEXT    NOT NULL UNIQUE,
                    senha_hash  TEXT    NOT NULL,
                    tipo        TEXT    NOT NULL DEFAULT 'inquilino',
                    ativo       INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS configuracao (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def segredo(self, chave: str) -> str:
        conn = self.connect()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO configuracao (chave, valor) VALUES (?, ?)",
                (chave, secrets.token_hex(32)),
            )
            conn.commit()
            return conn.execute(
                "SELECT valor FROM configuracao WHERE chave = ?", (chave,)
            ).fetchone()["valor"]
        finally:
            conn.close()
