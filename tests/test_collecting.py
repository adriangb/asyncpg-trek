import pathlib
from dataclasses import dataclass
from typing import Any, Collection, List

import pytest

from asyncpg_trek._collect import collect_migrations_from_filesystem
from asyncpg_trek._types import Direction, Migration
from tests.backend import InMemoryBackend


async def placeholder_op(conn: Any) -> None:
    ...


@dataclass(frozen=True, order=True)
class SimpleMig:
    from_rev: str
    to_rev: str
    direction: Direction


def simplify(migrations: Collection[Migration[Any]]) -> List[SimpleMig]:
    return [SimpleMig(m.from_rev, m.to_rev, m.direction) for m in migrations]


def test_collect() -> None:
    backend = InMemoryBackend()
    migrations = collect_migrations_from_filesystem(
        pathlib.Path(__file__).parent / "sqlite_revisions", backend
    )
    simplified = simplify(migrations)
    expected = [
        SimpleMig("initial", "rev1", Direction.up),
        SimpleMig("rev1", "rev2", Direction.up),
        SimpleMig("rev2", "rev3", Direction.up),
        SimpleMig("rev3", "rev4", Direction.up),
        SimpleMig("rev4", "rev5", Direction.up),
        SimpleMig("rev2", "rev1", Direction.down),
        SimpleMig("rev1", "initial", Direction.down),
        SimpleMig("rev5", "rev4", Direction.down),
    ]
    expected.sort()
    simplified.sort()
    assert simplified == expected


def test_collect_no_revisions() -> None:
    backend = InMemoryBackend()
    with pytest.raises(LookupError):
        collect_migrations_from_filesystem(
            pathlib.Path(__file__).parent / "revisions_no_revisions", backend
        )
