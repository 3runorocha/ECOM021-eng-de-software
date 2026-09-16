import sqlite3

from database import Database
from models import Notificacao, NotificacaoCreate


class NotificacaoRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_notificacao(row: sqlite3.Row) -> Notificacao:
        return Notificacao(**dict(row))

    def buscar_por_id(self, notificacao_id: int) -> Notificacao | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM notificacoes WHERE id = ?", (notificacao_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_notificacao(row) if row else None

    def listar_por_usuario(
        self, usuario_id: int, apenas_nao_lidas: bool = False
    ) -> list[Notificacao]:
        query = "SELECT * FROM notificacoes WHERE usuario_id = ?"
        if apenas_nao_lidas:
            query += " AND lida = 0"
        query += " ORDER BY data_criacao DESC"

        conn = self._db.connect()
        try:
            rows = conn.execute(query, (usuario_id,)).fetchall()
        finally:
            conn.close()
        return [self._to_notificacao(r) for r in rows]

    def existe_nao_lida(
        self, usuario_id: int, livro_id: int, tipos: tuple[str, ...]
    ) -> bool:
        placeholders = ", ".join("?" for _ in tipos)
        conn = self._db.connect()
        try:
            row = conn.execute(
                f"""
                SELECT id FROM notificacoes
                WHERE usuario_id = ? AND livro_id = ? AND lida = 0
                  AND tipo IN ({placeholders})
                """,
                (usuario_id, livro_id, *tipos),
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    def inserir(self, dados: NotificacaoCreate) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO notificacoes (usuario_id, tipo, mensagem, livro_id)
                VALUES (?, ?, ?, ?)
                """,
                (dados.usuario_id, dados.tipo, dados.mensagem, dados.livro_id),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def marcar_como_lida(self, notificacao_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                "UPDATE notificacoes SET lida = 1 WHERE id = ?", (notificacao_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def marcar_todas_como_lidas(self, usuario_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                "UPDATE notificacoes SET lida = 1 WHERE usuario_id = ?",
                (usuario_id,),
            )
            conn.commit()
        finally:
            conn.close()