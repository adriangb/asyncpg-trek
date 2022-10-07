import pathlib
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Awaitable, Callable, Optional

import asyncpg  # type: ignore

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


class AsyncpgBackend:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    def connect(self) -> AsyncContextManager[asyncpg.Connection]:
        @asynccontextmanager
        async def cm() -> AsyncIterator[asyncpg.Connection]:
            async with self.connection.transaction(isolation="serializable"):  # type: ignore
                yield self.connection

        return cm()

    async def create_table_idempotent(self, connection: asyncpg.Connection) -> None:
        await connection.execute(CREATE_TABLE)  # type: ignore

    async def get_current_revision(
        self, connection: asyncpg.Connection
    ) -> Optional[str]:
        return await connection.fetchval(GET_CURRENT_REVISION)  # type: ignore

    async def record_migration(
        self,
        connection: asyncpg.Connection,
        *,
        from_revision: Optional[str],
        to_revision: Optional[str]
    ) -> None:
        await connection.execute(RECORD_REVISION, from_revision, to_revision)  # type: ignore

    def execute_sql_file(
        self, path: pathlib.Path
    ) -> Callable[[asyncpg.Connection], Awaitable[None]]:
        async def exec(connection: asyncpg.Connection) -> None:
            with open(path) as f:
                query = f.read()

            await connection.execute(query)  # type: ignore

        return exec
