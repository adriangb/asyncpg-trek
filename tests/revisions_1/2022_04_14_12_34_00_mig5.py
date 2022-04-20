import asyncpg  # type: ignore[import]


async def upgrade(conn: asyncpg.Connection) -> None:
    await conn.execute("CREATE INDEX name_idx ON test(name)")  # type: ignore


async def downgrade(conn: asyncpg.Connection) -> None:
    await conn.execute("DROP INDEX name_idx")  # type: ignore
