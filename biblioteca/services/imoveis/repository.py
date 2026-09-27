import sqlite3

from database import Database
from models import Imovel, ImovelCreate
from exceptions import RegraDeNegocio


class ImovelRepository:

    def __init__(self, database: Database):
        self._db = database

    @staticmethod
    def _to_imovel(row: sqlite3.Row) -> Imovel:
        dados = dict(row)
        # SQLite nao tem booleano: a coluna guarda 0/1.
        dados["disponivel"] = bool(dados["disponivel"])
        return Imovel(**dados)

    def listar(
        self,
        cidade: str = None,
        tipo: str = None,
        quartos_min: int = None,
        valor_min: float = None,
        valor_max: float = None,
        disponivel: bool = None,
    ) -> list[Imovel]:
        query = "SELECT * FROM imoveis"
        condicoes = []
        params = []

        if cidade:
            condicoes.append("cidade LIKE ?")
            params.append(f"%{cidade}%")
        if tipo:
            condicoes.append("tipo = ?")
            params.append(tipo)
        if quartos_min is not None:
            condicoes.append("quartos >= ?")
            params.append(quartos_min)
        if valor_min is not None:
            condicoes.append("valor_mensal >= ?")
            params.append(valor_min)
        if valor_max is not None:
            condicoes.append("valor_mensal <= ?")
            params.append(valor_max)
        if disponivel is not None:
            condicoes.append("disponivel = ?")
            params.append(int(disponivel))

        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)
        query += " ORDER BY valor_mensal"

        conn = self._db.connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            conn.close()
        return [self._to_imovel(r) for r in rows]

    def buscar_por_id(self, imovel_id: int) -> Imovel | None:
        conn = self._db.connect()
        try:
            row = conn.execute(
                "SELECT * FROM imoveis WHERE id = ?", (imovel_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._to_imovel(row) if row else None

    def inserir(self, dados: ImovelCreate, disponivel: bool = True) -> int:
        conn = self._db.connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO imoveis
                    (titulo, tipo, endereco, cidade, quartos,
                     banheiros, area_m2, valor_mensal, disponivel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dados.titulo, dados.tipo, dados.endereco, dados.cidade,
                    dados.quartos, dados.banheiros, dados.area_m2,
                    dados.valor_mensal, int(disponivel),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            raise RegraDeNegocio(f"Erro ao cadastrar imóvel: {str(e)}")
        finally:
            conn.close()

    def atualizar(self, imovel_id: int, campos: dict) -> None:
        if not campos:
            return
        set_clause = ", ".join(f"{k} = ?" for k in campos)
        valores = list(campos.values()) + [imovel_id]
        conn = self._db.connect()
        try:
            conn.execute(
                f"UPDATE imoveis SET {set_clause} WHERE id = ?", valores
            )
            conn.commit()
        finally:
            conn.close()

    def remover(self, imovel_id: int) -> None:
        conn = self._db.connect()
        try:
            conn.execute("DELETE FROM imoveis WHERE id = ?", (imovel_id,))
            conn.commit()
        finally:
            conn.close()
