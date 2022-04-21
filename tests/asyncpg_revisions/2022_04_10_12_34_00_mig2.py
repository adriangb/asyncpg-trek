import asyncpg  # type: ignore[import]


async def upgrade(conn: asyncpg.Connection) -> None:
    await conn.execute("CREATE INDEX name_idx ON people(name)")  # type: ignore
    await conn.execute("INSERT INTO people(name) VALUES ('Anakin')")  # type: ignore
