import pathlib
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Optional

from asyncpg_trek import Operation

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    from_revision TEXT,
    to_revision TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""


GET_CURRENT_REVISION = """\
SELECT to_revision
FROM migrations
ORDER BY id DESC
LIMIT 1;
"""


class InMemoryBackendExecutor:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    async def create_table_idempotent(self) -> None:
        self.connection.execute(CREATE_TABLE)

    async def get_current_revision(self) -> Optional[str]:
        cur = self.connection.cursor()
        cur.execute(GET_CURRENT_REVISION)
        res = cur.fetchone()
        if not res:
            return None
        return next(iter(res))  # type: ignore[no-any-return]

    async def record_migration(
        self,
        from_revision: Optional[str],
        to_revision: Optional[str],
    ) -> None:
        self.connection.execute(
            "INSERT INTO migrations(from_revision, to_revision) VALUES (?, ?)",
            (from_revision, to_revision),
        )

    async def execute_operation(self, operation: Operation[sqlite3.Connection]) -> None:
        await operation(self.connection)


class InMemoryBackend:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")

    def connect(self) -> AsyncContextManager[InMemoryBackendExecutor]:
        @asynccontextmanager
        async def cm() -> AsyncIterator[InMemoryBackendExecutor]:
            with self.connection:
                yield InMemoryBackendExecutor(self.connection)

        return cm()

    def prepare_operation_from_sql_file(
        self, path: pathlib.Path
    ) -> Operation[sqlite3.Connection]:
        async def operation(connection: sqlite3.Connection) -> None:
            with open(path) as f:
                query = f.read()
            connection.execute(query)

        return operation
