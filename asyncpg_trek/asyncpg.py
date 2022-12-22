import pathlib
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Optional

import asyncpg  # type: ignore

from asyncpg_trek._types import Operation

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    from_revision TEXT,
    to_revision TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp
);
CREATE INDEX ON migrations(timestamp);
"""


GET_CURRENT_REVISION = """\
SELECT to_revision
FROM migrations
ORDER BY id DESC
LIMIT 1;
"""

RECORD_REVISION = """\
INSERT INTO migrations(from_revision, to_revision)
VALUES ($1, $2)
"""


class AsyncpgExecutor:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    async def create_table_idempotent(self) -> None:
        await self.connection.execute(CREATE_TABLE)  # type: ignore

    async def get_current_revision(self) -> Optional[str]:
        return await self.connection.fetchval(GET_CURRENT_REVISION)  # type: ignore

    async def record_migration(
        self, from_revision: Optional[str], to_revision: Optional[str]
    ) -> None:
        await self.connection.execute(RECORD_REVISION, from_revision, to_revision)  # type: ignore

    async def execute_operation(self, operation: Operation[asyncpg.Connection]) -> None:
        await operation(self.connection)


class AsyncpgBackend:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    def connect(self) -> AsyncContextManager[AsyncpgExecutor]:
        @asynccontextmanager
        async def cm() -> AsyncIterator[AsyncpgExecutor]:
            async with self.connection.transaction(isolation="serializable"):  # type: ignore
                yield AsyncpgExecutor(self.connection)

        return cm()

    def prepare_operation_from_sql_file(
        self, path: pathlib.Path
    ) -> Operation[asyncpg.Connection]:
        async def operation(connection: asyncpg.Connection) -> None:
            with open(path) as f:
                query = f.read()

            await connection.execute(query)  # type: ignore

        return operation
