import sqlite3

from database import Database
from models import Contrato, STATUS_EM_ABERTO
from exceptions import RegraDeNegocio


class ContratoRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_contrato(row: sqlite3.Row) -> Contrato:
        return Contrato(**dict(row))

    def buscar_por_id(self, contrato_id: int) -> Contrato | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM contratos WHERE id = ?", (contrato_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_contrato(row) if row else None

    def existe_aberto(self, imovel_id: int) -> bool:
        """Um imovel so pode ter um contrato em aberto, seja quem for o inquilino.

        Diferente do acervo de livros, onde a checagem era por (usuario, livro)
        porque havia varios exemplares do mesmo titulo.
        """
        marcadores = ", ".join("?" for _ in STATUS_EM_ABERTO)
        conn = self._db.connect()
        try:
            row = conn.execute(
                f"SELECT id FROM contratos WHERE imovel_id = ? "
                f"AND status IN ({marcadores})",
                (imovel_id, *STATUS_EM_ABERTO),
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    def listar(self, inquilino_id: int = None, status: str = None) -> list[Contrato]:
        query = "SELECT * FROM contratos"
        condicoes = []
        params = []

        if inquilino_id:
            condicoes.append("inquilino_id = ?")
            params.append(inquilino_id)
        if status:
            condicoes.append("status = ?")
            params.append(status)

        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)
        query += " ORDER BY data_inicio DESC"

        conn = self._db.connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        return [self._to_contrato(r) for r in rows]

    def inserir(
        self,
        inquilino_id: int,
        imovel_id: int,
        data_inicio: str,
        data_fim_prevista: str,
        valor_mensal: float,
    ) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO contratos
                    (inquilino_id, imovel_id, data_inicio,
                     data_fim_prevista, valor_mensal, status)
                VALUES (?, ?, ?, ?, ?, 'ativo')
                """,
                (inquilino_id, imovel_id, data_inicio, data_fim_prevista, valor_mensal),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # O indice parcial barrou: o imovel ganhou um contrato aberto entre
            # a checagem do servico e este INSERT.
            raise RegraDeNegocio(
                f"Imóvel {imovel_id} já possui contrato em aberto"
            )
        finally:
            conn.close()

    def encerrar(self, contrato_id: int, data_fim_real: str, multa: float) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                UPDATE contratos
                SET data_fim_real = ?, status = 'encerrado', multa = ?
                WHERE id = ?
                """,
                (data_fim_real, multa, contrato_id),
            )
            conn.commit()
        finally:
            conn.close()

    def marcar_atrasados(self) -> None:
        conn = self._db.connect()
        try:
            conn.execute(
                """
                UPDATE contratos
                SET status = 'atrasado'
                WHERE status = 'ativo'
                  AND data_fim_prevista < date('now')
                """
            )
            conn.commit()
        finally:
            conn.close()
