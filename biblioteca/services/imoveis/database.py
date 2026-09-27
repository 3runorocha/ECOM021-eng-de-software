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
                CREATE TABLE IF NOT EXISTS imoveis (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo       TEXT    NOT NULL,
                    tipo         TEXT    NOT NULL,
                    endereco     TEXT    NOT NULL,
                    cidade       TEXT    NOT NULL,
                    quartos      INTEGER NOT NULL,
                    banheiros    INTEGER NOT NULL,
                    area_m2      REAL    NOT NULL,
                    valor_mensal REAL    NOT NULL,
                    disponivel   INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
