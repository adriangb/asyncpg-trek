from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import asyncpg  # type: ignore[import]
import pytest

from asyncpg_trek import Direction, execute, plan
from asyncpg_trek.asyncpg import AsyncpgBackend


@pytest.fixture
@pytest.mark.anyio
async def admin_connection() -> AsyncIterator[asyncpg.Connection]:
    async with asyncpg.create_pool(  # type: ignore
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    ) as pool:
        conn: asyncpg.Connection
        async with pool.acquire() as conn:  # type: ignore
            yield conn


@pytest.fixture
@pytest.mark.anyio
async def db_connection(
    admin_connection: asyncpg.Connection,
) -> AsyncIterator[asyncpg.Connection]:
    db_name = f'tmp_{str(uuid4()).replace("-", "_")}'
    await admin_connection.execute(f"CREATE DATABASE {db_name}")  # type: ignore
    try:
        async with asyncpg.create_pool(  # type: ignore
            host="localhost",
            port=5433,
            user="postgres",
            password="postgres",
            database=db_name,
        ) as pool:
            conn: asyncpg.Connection
            async with pool.acquire() as conn:  # type: ignore
                yield conn
    finally:
        await admin_connection.execute(f"DROP DATABASE {db_name}")  # type: ignore


MIGRATIONS_FOLDER = Path(__file__).parent / "asyncpg_revisions"


@pytest.mark.parametrize("schema", [None, "custom"])
@pytest.mark.anyio
async def test_run_migrations(db_connection: asyncpg.Connection, schema: str) -> None:
    backend = AsyncpgBackend(db_connection, schema)
    async with backend.connect() as conn:
        planned = await plan(conn, backend, MIGRATIONS_FOLDER, "rev1", Direction.up)
        await execute(conn, backend, planned)
        record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
        assert record is None

        planned = await plan(conn, backend, MIGRATIONS_FOLDER, "rev2", Direction.up)
        await execute(conn, backend, planned)
        record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
        assert record and record["name"] == "Anakin"  # type: ignore


@pytest.mark.parametrize("schema", [None, "custom"])
@pytest.mark.anyio
async def test_run_migrations_failure(
    db_connection: asyncpg.Connection, schema: str
) -> None:
    backend = AsyncpgBackend(db_connection, schema)
    async with backend.connect() as conn:
        planned = await plan(conn, backend, MIGRATIONS_FOLDER, "rev2", Direction.up)
        await execute(conn, backend, planned)
        record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
        assert record and record["name"] == "Anakin"  # type: ignore

    async with backend.connect() as conn:
        # rev3 deletes everything
        planned = await plan(conn, backend, MIGRATIONS_FOLDER, "rev3", Direction.up)
        await execute(conn, backend, planned)
        record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
        assert record is None

        planned = await plan(conn, backend, MIGRATIONS_FOLDER, "rev4bad", Direction.up)
        # exceptions should be propagated up
        with pytest.raises(asyncpg.UndefinedTableError):
            await execute(conn, backend, planned)

    async with backend.connect() as conn:
        # the changes should be reverted because migrations are run in a transaction
        record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
        assert record and record["name"] == "Anakin"  # type: ignore
