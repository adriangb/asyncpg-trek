import sqlite3


async def run_migration(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO people(name, nickname) VALUES ('Anakin Skywalker', 'Ani')"
    )
