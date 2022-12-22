import pathlib
from logging import getLogger
from typing import Sequence, TypeVar, Union

from asyncpg_trek._backend import SupportsBackend
from asyncpg_trek._collect import collect_migrations_from_filesystem
from asyncpg_trek._solver import find_migration_path
from asyncpg_trek._types import Direction as MigrationDirection
from asyncpg_trek._types import Migration

logger = getLogger(__name__)


T = TypeVar("T")


class Plan:
    def __init__(
        self,
        backend: SupportsBackend[T],
        planned_migrations: Sequence[Migration[T]],
    ) -> None:
        self.backend = backend
        self.planned_migrations = planned_migrations


async def plan(
    backend: SupportsBackend[T],
    directory: Union[str, pathlib.Path],
    target_revision: str,
    direction: MigrationDirection,
) -> Plan:
    migrations = collect_migrations_from_filesystem(pathlib.Path(directory), backend)
    rev_list = "\n".join([f" - {m.from_rev} -> {m.to_rev}" for m in migrations])
    logger.debug(f"Collected migrations from {directory}: {rev_list}")
    logger.debug("Creating migrations table")
    await backend.create_table_idempotent()
    logger.debug("Getting current revision")
    current_revision = await backend.get_current_revision()
    if current_revision:
        logger.info(f"Current revision is {current_revision}")
    else:
        current_revision = "initial"
        logger.info("No existing revisions found, starting from scratch")
    migrations = find_migration_path(
        current_revision, target_revision, direction=direction, migrations=migrations
    )
    return Plan(
        backend=backend,
        planned_migrations=migrations,
    )


async def execute(plan: Plan) -> None:
    for mig in plan.planned_migrations:
        logger.info(f"Running {mig.from_rev} -> {mig.to_rev}")
        await plan.backend.record_migration(
            from_revision=mig.from_rev,
            to_revision=mig.to_rev,
        )
        await mig.operation()
        logger.info(f"{mig.from_rev} -> {mig.to_rev} OK")
