import sqlite3

from database import Database
from models import Livro, LivroCreate
from exceptions import RegraDeNegocio


class LivroRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_livro(row: sqlite3.Row) -> Livro:
        return Livro(**dict(row))

    def listar(self, genero: str = None, autor: str = None) -> list[Livro]:
        query = "SELECT * FROM livros"
        condicoes = []
        params = []

        if genero:
            condicoes.append("genero = ?")
            params.append(genero)
        if autor:
            condicoes.append("autor LIKE ?")
            params.append(f"%{autor}%")

        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)

        conn = self._db.connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        return [self._to_livro(r) for r in rows]

    def buscar_por_id(self, livro_id: int) -> Livro | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM livros WHERE id = ?", (livro_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_livro(row) if row else None

    def buscar_por_isbn(self, isbn: str) -> Livro | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM livros WHERE isbn = ?", (isbn,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_livro(row) if row else None

    def inserir(self, dados: LivroCreate, quantidade_disponivel: int) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO livros
                    (titulo, autor, isbn, ano_publicacao, genero,
                     quantidade_total, quantidade_disponivel)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dados.titulo, dados.autor, dados.isbn,
                    dados.ano_publicacao, dados.genero,
                    dados.quantidade_total, quantidade_disponivel,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise RegraDeNegocio(f"Erro ao cadastrar livro: {str(e)}")
        finally:
            conn.close()

    def atualizar(self, livro_id: int, campos: dict) -> None:
        if not campos:
            return
        set_clause = ", ".join(f"{k} = ?" for k in campos)
        valores = list(campos.values()) + [livro_id]
        conn = self._db.connect()
        try:
            conn.execute(
                f"UPDATE livros SET {set_clause} WHERE id = ?", valores
            )
            conn.commit()
        finally:
            conn.close()

    def remover(self, livro_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
            conn.commit()
        finally:
            conn.close()