import sqlite3

from database import Database
from models import UsuarioPublico
from exceptions import RegraDeNegocio


class UsuarioRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_publico(row: sqlite3.Row) -> UsuarioPublico:
        dados = dict(row)
        dados.pop("senha_hash", None)
        return UsuarioPublico(**dados)

    def buscar_por_id(self, usuario_id: int) -> UsuarioPublico | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_publico(row) if row else None

    def listar(self) -> list[UsuarioPublico]:
        conn = self._db.connect()
        try:
            rows = conn.execute("SELECT * FROM usuarios").fetchall()
        finally:
            conn.close()
        return [self._to_publico(r) for r in rows]

    def buscar_ativo_com_hash(
        self, email: str
    ) -> tuple[UsuarioPublico, str] | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,)
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        dados = dict(row)
        senha_hash = dados.pop("senha_hash")
        return UsuarioPublico(**dados), senha_hash

    def existe_algum(self) -> bool:
        conn = self._db.connect()
        try:
            return conn.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() is not None
        finally:
            conn.close()

    def inserir(self, nome: str, email: str, senha_hash: str, tipo: str) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, tipo)
                VALUES (?, ?, ?, ?)
                """,
                (nome, email, senha_hash, tipo),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise RegraDeNegocio(
                f"Email já cadastrado ou dados inválidos: {str(e)}"
            )
        finally:
            conn.close()

    def atualizar(self, usuario_id: int, campos: dict) -> None:
        if not campos:
            return
        set_clause = ", ".join(f"{k} = ?" for k in campos)
        valores = list(campos.values()) + [usuario_id]
        conn = self._db.connect()
        try:
            conn.execute(
                f"UPDATE usuarios SET {set_clause} WHERE id = ?", valores
            )
            conn.commit()
        finally:
            conn.close()
