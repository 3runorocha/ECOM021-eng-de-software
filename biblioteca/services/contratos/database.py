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
                CREATE TABLE IF NOT EXISTS contratos (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    inquilino_id      INTEGER NOT NULL,
                    imovel_id         INTEGER NOT NULL,
                    data_inicio       TEXT    NOT NULL,
                    data_fim_prevista TEXT    NOT NULL,
                    data_fim_real     TEXT,
                    valor_mensal      REAL    NOT NULL,
                    status            TEXT    NOT NULL DEFAULT 'ativo',
                    multa             REAL    NOT NULL DEFAULT 0.0
                )
                """
            )
            # Um imovel so pode ter um contrato em aberto. O indice parcial deixa
            # o banco impor a regra, alem da checagem no servico: se duas
            # requisicoes passarem pela checagem ao mesmo tempo, a segunda falha
            # no INSERT em vez de gerar contrato duplicado.
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_um_contrato_aberto
                ON contratos (imovel_id)
                WHERE status IN ('ativo', 'atrasado')
                """
            )
            conn.commit()
        finally:
            conn.close()
