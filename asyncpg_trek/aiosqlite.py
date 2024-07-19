import pathlib
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Optional

import aiosqlite

from asyncpg_trek._types import Operation

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    from_revision TEXT,
    to_revision TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp
)"""
CREATE_INDEX = """\
CREATE INDEX IF NOT EXISTS migrations_timestamp_idx ON migrations(timestamp);
"""

GET_CURRENT_REVISION = """\
SELECT to_revision
FROM migrations
ORDER BY id DESC
LIMIT 1
"""

RECORD_REVISION = """\
INSERT INTO migrations(from_revision, to_revision)
VALUES ($1, $2)
"""


class AiosqliteExecutor:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def create_table_idempotent(self) -> None:
        await self.connection.execute(CREATE_TABLE)  # type: ignore
        await self.connection.execute(CREATE_INDEX)

    async def get_current_revision(self) -> Optional[str]:
        async with self.connection.execute(GET_CURRENT_REVISION) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]  # type: ignore
            return None

    async def record_migration(
        self, from_revision: Optional[str], to_revision: Optional[str]
    ) -> None:
        await self.connection.execute(RECORD_REVISION, (from_revision, to_revision))  # type: ignore

    async def execute_operation(
        self, operation: Operation[aiosqlite.Connection]
    ) -> None:
        await operation(self.connection)


class AiosqliteBackend:
    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    def connect(self) -> AsyncContextManager[AiosqliteExecutor]:
        @asynccontextmanager
        async def cm() -> AsyncIterator[AiosqliteExecutor]:
            yield AiosqliteExecutor(self.connection)

        return cm()

    def prepare_operation_from_sql_file(
        self, path: pathlib.Path
    ) -> Operation[aiosqlite.Connection]:
        async def operation(connection: aiosqlite.Connection) -> None:
            with open(path) as f:
                query = f.read()

            await connection.execute(query)  # type: ignore

        return operation
