import sqlite3

from database import Database
from models import Emprestimo


class EmprestimoRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_emprestimo(row: sqlite3.Row) -> Emprestimo:
        return Emprestimo(**dict(row))

    def buscar_por_id(self, emprestimo_id: int) -> Emprestimo | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM emprestimos WHERE id = ?", (emprestimo_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_emprestimo(row) if row else None

    def existe_ativo(self, usuario_id: int, livro_id: int) -> bool:
        conn = self._db.connect()
        try:
            row = conn.execute(
                """
                SELECT id FROM emprestimos
                WHERE usuario_id = ? AND livro_id = ? AND status != 'devolvido'
                """,
                (usuario_id, livro_id),
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    def listar(self, usuario_id: int = None, status: str = None) -> list[Emprestimo]:
        query = "SELECT * FROM emprestimos"
        condicoes = []
        params = []

        if usuario_id:
            condicoes.append("usuario_id = ?")
            params.append(usuario_id)
        if status:
            condicoes.append("status = ?")
            params.append(status)

        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)

        conn = self._db.connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        return [self._to_emprestimo(r) for r in rows]

    def inserir(
        self,
        usuario_id: int,
        livro_id: int,
        data_emprestimo: str,
        data_devolucao_prevista: str,
    ) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO emprestimos
                    (usuario_id, livro_id, data_emprestimo,
                     data_devolucao_prevista, status)
                VALUES (?, ?, ?, ?, 'ativo')
                """,
                (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def registrar_devolucao(
        self, emprestimo_id: int, data_devolucao_real: str, multa: float
    ) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                UPDATE emprestimos
                SET data_devolucao_real = ?, status = 'devolvido', multa = ?
                WHERE id = ?
                """,
                (data_devolucao_real, multa, emprestimo_id),
            )
            conn.commit()
        finally:
            conn.close()

    def marcar_atrasados(self) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                UPDATE emprestimos
                SET status = 'atrasado'
                WHERE status = 'ativo'
                  AND data_devolucao_prevista < date('now')
                """
            )
            conn.commit()
        finally:
            conn.close()