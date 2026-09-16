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
                CREATE TABLE IF NOT EXISTS livros (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo                TEXT    NOT NULL,
                    autor                 TEXT    NOT NULL,
                    isbn                  TEXT    NOT NULL UNIQUE,
                    ano_publicacao        INTEGER NOT NULL,
                    genero                TEXT    NOT NULL,
                    quantidade_total      INTEGER NOT NULL DEFAULT 1,
                    quantidade_disponivel INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.commit()
        finally:
            conn.close()