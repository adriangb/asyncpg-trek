import pathlib
from logging import getLogger
from typing import Any, Optional, Union

from asyncpg_trek._backend import SupportsBackend
from asyncpg_trek._collect import collect_sorted_versions
from asyncpg_trek._solver import find_migration_path

logger = getLogger(__name__)


async def run(
    backend: SupportsBackend[Any],
    directory: Union[str, pathlib.Path],
    *,
    target_revision: Optional[str] = "HEAD",
) -> None:
    revisions = collect_sorted_versions(pathlib.Path(directory), backend)
    logger.debug(
        f"Collected revisions from {directory}: {[r.revision for r in revisions]}"
    )
    async with backend.connect() as conn:
        logger.debug("Creating migrations table")
        await backend.create_table(conn)
        logger.debug("Getting current revision")
        current_revision = await backend.get_current_revision(conn)
        if current_revision:
            logger.info(f"Current revision is {current_revision}")
        else:
            logger.info("No existing revisions found, starting from scratch")
        maybe_migration_path = find_migration_path(
            current_revision, target_revision, revisions
        )
        if maybe_migration_path is None:
            logger.info("No migrations necessary")
            return
        direction, migration_path = maybe_migration_path
        path_txt = "".join(
            [
                f"{node.from_revision.revision if node.from_revision else ''}"
                + (" ->" if node.from_revision else "")
                + f" {node.to_revision.revision if node.to_revision else ''}"
                for node in migration_path
            ]
        )
        msg_dir = {"up": "Upgrade", "down": "Downgrade"}[direction]
        logger.info(f"{msg_dir} path calculated: {path_txt}")
        for node in migration_path:
            from_rev, to_rev, operation = (
                node.from_revision,
                node.to_revision,
                node.operation,
            )
            from_rev_txt = from_rev.revision if from_rev else ""
            to_rev_txt = to_rev.revision if to_rev else ""
            logger.info(f"Running {from_rev_txt} -> {to_rev_txt}")
            await backend.record_migration(
                conn,
                from_revision=from_rev.revision if from_rev else None,
                to_revision=to_rev.revision if to_rev else None,
            )
            await operation(conn)
            logger.info(f"{from_rev_txt} -> {to_rev_txt} OK")
