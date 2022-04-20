import pathlib
import sqlite3
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Awaitable, Callable, Optional

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


class InMemoryBackend:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")

    def connect(self) -> AsyncContextManager[sqlite3.Connection]:
        @asynccontextmanager
        async def cm() -> AsyncIterator[sqlite3.Connection]:
            with self.connection:
                yield self.connection

        return cm()

    async def create_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(CREATE_TABLE)

    async def get_current_revision(
        self, connection: sqlite3.Connection
    ) -> Optional[str]:
        cur = connection.cursor()
        cur.execute(GET_CURRENT_REVISION)
        res = cur.fetchone()
        if not res:
            return None
        return next(iter(res))  # type: ignore[no-any-return]

    async def record_migration(
        self,
        connection: sqlite3.Connection,
        *,
        from_revision: Optional[str],
        to_revision: Optional[str],
    ) -> None:
        connection.execute(
            f"INSERT INTO migrations(from_revision, to_revision) VALUES (?, ?)",
            (from_revision, to_revision),
        )

    def execute_sql_file(
        self, path: pathlib.Path
    ) -> Callable[[sqlite3.Connection], Awaitable[None]]:
        async def exec(connection: sqlite3.Connection) -> None:
            with open(path) as f:
                query = f.read()
            connection.execute(query)

        return exec
