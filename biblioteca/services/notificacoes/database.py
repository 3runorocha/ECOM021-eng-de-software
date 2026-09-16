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
                CREATE TABLE IF NOT EXISTS notificacoes (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id   INTEGER NOT NULL,
                    tipo         TEXT    NOT NULL,
                    mensagem     TEXT    NOT NULL,
                    livro_id     INTEGER,
                    lida         INTEGER NOT NULL DEFAULT 0,
                    data_criacao TEXT    NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()
        finally:
            conn.close()