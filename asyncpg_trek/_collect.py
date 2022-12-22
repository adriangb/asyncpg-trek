import pathlib
import re
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from typing import Collection, Generic, List, TypeVar, cast

from asyncpg_trek._backend import SupportsBackend
from asyncpg_trek._types import INITIAL_REVISION, Direction, Migration, Operation

T = TypeVar("T")

MIGRATION_FILE_PATT = re.compile(
    r"^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_(?P<from>\w+)_(?P<direction>(:?up)|(:?down))_(?P<to>\w+).(?P<format>(:?sql)|(:?py))$"
)


@dataclass
class CollectedMigrations(Generic[T]):
    migrations: Collection[Migration[T]]
    initial: Migration[T]


def collect_migrations_from_filesystem(
    revisions_folder: pathlib.Path, backend: SupportsBackend[T]
) -> Collection[Migration[T]]:
    found_initial = False
    migrations: List[Migration[T]] = []
    for path in revisions_folder.iterdir():
        if not path.is_file():
            continue
        match = MIGRATION_FILE_PATT.match(path.name)
        if not match:
            continue
        format = match.group("format")
        if match.group("direction") == "up":
            direction = Direction.up
        else:
            direction = Direction.down
        from_rev, to_rev = match.group("from"), match.group("to")
        if format == "py":
            mod = SourceFileLoader(path.stem, str(path.absolute())).load_module()
            operation = cast(Operation[T], getattr(mod, "run_migration"))
            mig = Migration(
                operation=operation,
                from_rev=from_rev,
                to_rev=to_rev,
                direction=direction,
            )
        else:
            operation = backend.prepare_operation_from_sql_file(path)
            mig = Migration(
                operation=operation,
                from_rev=from_rev,
                to_rev=to_rev,
                direction=direction,
            )
        if mig.from_rev == INITIAL_REVISION:
            found_initial = True
        migrations.append(mig)
    if not found_initial:
        raise LookupError("Unable to locate initial migration")
    return migrations
