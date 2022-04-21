from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import asyncpg  # type: ignore[import]
import pytest

from asyncpg_trek.asyncpg import AsyncpgBackend
from asyncpg_trek import run


@pytest.fixture
@pytest.mark.asyncio
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
@pytest.mark.asyncio
async def db_connection(admin_connection: asyncpg.Connection) -> AsyncIterator[asyncpg.Connection]:
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


@pytest.mark.asyncio
async def test_run_migrations(db_connection: asyncpg.Connection) -> None:
    backend = AsyncpgBackend(db_connection)
    await run(backend, MIGRATIONS_FOLDER, target_revision="2022_04_10_12_34_00_mig1")
    record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
    assert record is None
    await run(backend, MIGRATIONS_FOLDER, target_revision="2022_04_10_12_34_00_mig2")
    record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
    assert record["name"] == "Anakin"


@pytest.mark.asyncio
async def test_run_migrations_failure(db_connection: asyncpg.Connection) -> None:
    backend = AsyncpgBackend(db_connection)
    await run(backend, MIGRATIONS_FOLDER, target_revision="2022_04_10_12_34_00_mig2")
    record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
    assert record["name"] == "Anakin"

    # exceptions should be propagated up
    with pytest.raises(asyncpg.UndefinedTableError):
        await run(backend, MIGRATIONS_FOLDER, target_revision="2022_04_10_12_34_00_mig3_bad_migration")
    
    # the changes should be reverted because migrations are run in a transaction
    record = await db_connection.fetchrow("SELECT name FROM people LIMIT 1")  # type: ignore
    assert record["name"] == "Anakin"
