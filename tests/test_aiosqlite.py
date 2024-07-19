from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import aiosqlite
import pytest

from asyncpg_trek import Direction, execute, plan
from asyncpg_trek.aiosqlite import AiosqliteBackend


@pytest.fixture
@pytest.mark.anyio
async def db_connection(tmp_path: Path) -> AsyncIterator[aiosqlite.Connection]:
    test_db = tmp_path / f"{uuid4()}.sqlite"
    async with aiosqlite.connect(test_db) as db:  # type: ignore
        yield db


MIGRATIONS_FOLDER_AIOSQLITE = Path(__file__).parent / "asyncpg_revisions"


@pytest.mark.anyio
async def test_run_migrations(db_connection: aiosqlite.Connection) -> None:
    backend = AiosqliteBackend(db_connection)
    planned = await plan(backend, MIGRATIONS_FOLDER_AIOSQLITE, "rev1", Direction.up)
    await execute(backend, planned)
    async with db_connection.execute("SELECT name FROM people LIMIT 1") as c:
        record = await c.fetchone()
    assert record is None

    planned = await plan(backend, MIGRATIONS_FOLDER_AIOSQLITE, "rev2", Direction.up)
    await execute(backend, planned)

    async with db_connection.execute("SELECT name FROM people LIMIT 1") as c:
        record = await c.fetchone()
    assert record and record[0] == "Anakin"  # type: ignore


@pytest.mark.anyio
async def test_run_migrations_failure(db_connection: aiosqlite.Connection) -> None:
    backend = AiosqliteBackend(db_connection)
    planned = await plan(backend, MIGRATIONS_FOLDER_AIOSQLITE, "rev2", Direction.up)
    await execute(backend, planned)
    async with db_connection.execute("SELECT name FROM people LIMIT 1") as c:
        record = await c.fetchone()
    assert record and record[0] == "Anakin"  # type: ignore

    # rev3 deletes everything
    planned = await plan(backend, MIGRATIONS_FOLDER_AIOSQLITE, "rev3", Direction.up)
    await execute(backend, planned)
    async with db_connection.execute("SELECT name FROM people LIMIT 1") as c:
        record = await c.fetchone()
    assert record is None

    planned = await plan(backend, MIGRATIONS_FOLDER_AIOSQLITE, "rev4bad", Direction.up)
    # exceptions should be propagated up
    with pytest.raises(aiosqlite.DatabaseError):
        await execute(backend, planned)

    # the changes should be reverted because migrations are run in a transaction
    async with db_connection.execute("SELECT name FROM people LIMIT 1") as c:
        record = await c.fetchone()
    assert record is None
