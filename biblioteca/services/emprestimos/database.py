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
                CREATE TABLE IF NOT EXISTS emprestimos (
                    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id               INTEGER NOT NULL,
                    livro_id                 INTEGER NOT NULL,
                    data_emprestimo          TEXT    NOT NULL,
                    data_devolucao_prevista  TEXT    NOT NULL,
                    data_devolucao_real      TEXT,
                    status                   TEXT    NOT NULL DEFAULT 'ativo',
                    multa                    REAL    NOT NULL DEFAULT 0.0
                )
                """
            )
            conn.commit()
        finally:
            conn.close()