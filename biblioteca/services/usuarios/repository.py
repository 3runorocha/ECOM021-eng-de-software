import sqlite3

from database import Database
from models import UsuarioPublico
from exceptions import RegraDeNegocio


class UsuarioRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_publico(row: sqlite3.Row) -> UsuarioPublico:
        return UsuarioPublico(**dict(row))

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

    def buscar_por_credenciais(
        self, email: str, senha_hash: str
    ) -> UsuarioPublico | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                """
                SELECT * FROM usuarios
                WHERE email = ? AND senha_hash = ? AND ativo = 1
                """,
                (email, senha_hash),
            ).fetchone()
        finally:
            conn.close()
        return self._to_publico(row) if row else None

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
