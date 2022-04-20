import pathlib
from logging import getLogger
from typing import NewType, Optional, Union
import asyncpg  # type: ignore[import]

from asyncpg_trek._collect import collect_sorted_versions
from asyncpg_trek._solver import find_migration_path
from asyncpg_trek._typing import Literal


logger = getLogger(__name__)


CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS migrations (
    id SERIAL PRIMARY KEY,
    revision TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT current_timestamp
);
CREATE INDEX ON migrations(timestamp);
"""


GET_CURRENT_REVISION = """\
SELECT revision
FROM migrations
ORDER BY id DESC
LIMIT 1;
"""

RECORD_REVISION = """\
INSERT INTO migrations(revision)
VALUES ($1)
"""

TransactionIsolation = Literal["serializable", "read_committed", "repeatable_read"]

HEAD = NewType("HEAD", str)("HEAD")

async def run(
    *,
    conn: asyncpg.Connection,
    directory: Union[str, pathlib.Path],
    target_revision: Optional[str] = HEAD,
    transaction_isolation: TransactionIsolation = "serializable"
) -> None:
    revisions = collect_sorted_versions(pathlib.Path(directory))
    logger.debug(f"Collected revisions from {directory}: {[r.revision for r in revisions]}")
    if not revisions:
        raise ValueError("No migrations found")
    async with conn.transaction(isolation=transaction_isolation):  # type: ignore  # for Pylance
        logger.debug("Creating migrations table")
        await conn.execute(CREATE_TABLE)  # type: ignore  # for Pylance
        logger.debug("Getting current revision")
        current_revision: "Optional[str]" = await conn.fetchval(GET_CURRENT_REVISION)  # type: ignore  # for Pylance
        if current_revision:
            logger.info(f"Current revision is {current_revision}")
        else:
            logger.info("No existing revisions found, starting from scratch")
        maybe_migration_path = find_migration_path(current_revision, target_revision, revisions)
        if maybe_migration_path is None:
            logger.info("No migrations necessary")
            return
        direction, migration_path = maybe_migration_path
        path_txt = "->".join(
            [
                node.revision.revision
                for node in migration_path
            ]
        )
        msg_dir = {"up": "Upgrade", "down": "Downgrade"}[direction]
        logger.info(f"{msg_dir} path calculated: {path_txt}")
        for rev, operation in migration_path:
            logger.info(f"{rev.revision} {direction}")
            await conn.execute(RECORD_REVISION, rev.revision)  # type: ignore
            await operation(conn)
            logger.info(f"{rev.revision} {direction} OK")
