from database import Database


class RecomendacaoRepository:

    def __init__(self, database: Database):
        self._db = database

    def listar_recomendados(self, usuario_id: int) -> set[int]:
        conn = self._db.connect()
        try:
            rows = conn.execute(
                "SELECT imovel_id FROM historico_recomendacoes WHERE usuario_id = ?",
                (usuario_id,),
            ).fetchall()
        finally:
            conn.close()
        return {row["imovel_id"] for row in rows}

    def registrar_recomendacoes(
        self, usuario_id: int, imovel_ids: list[int]
    ) -> None:
        if not imovel_ids:
            return
        conn = self._db.connect()
        try:
            conn.executemany(
                """
                INSERT OR IGNORE INTO historico_recomendacoes (usuario_id, imovel_id)
                VALUES (?, ?)
                """,
                [(usuario_id, imovel_id) for imovel_id in imovel_ids],
            )
            conn.commit()
        finally:
            conn.close()