from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import asyncpg  # type: ignore[import]
import pytest

from asyncpg_trek._solver import MigrationNode, find_migration_path
from asyncpg_trek._revision import Revision
from asyncpg_trek._typing import Literal


Direction = Literal["up", "down"]


@dataclass
class Op:
    rev: int
    direction: Direction

    async def __call__(self, conn: asyncpg.Connection) -> None:
        ...



def rev(num: int, up: bool = True, down: bool = True) -> Revision:
    return Revision(
        f"{num}",
        upgrade=Op(num, "up") if up else None,
        downgrade=Op(num, "down") if down else None,
    )


def extract_path(got: Sequence[MigrationNode]) -> List[Op]:
    res: "List[Op]" = []
    for node in got:
        assert isinstance(node.operation, Op)
        res.append(node.operation)
    return res


@pytest.mark.parametrize(
    "revisions,current,target,expected_path", [
        ([rev(1)], None, None, None),
        ([rev(1)], None, "1", [(1, "up")]),
        ([rev(1)], None, "HEAD", [(1, "up")]),
        ([rev(1)], "1", None, [(1, "down")]),
        ([rev(1)], "1", "1", None),
        ([rev(1)], "1", "HEAD", None),

        ([rev(1), rev(2)], None, None, None),
        ([rev(1), rev(2)], None, "1", [(1, "up")]),
        ([rev(1), rev(2)], None, "2", [(1, "up"), (2, "up")]),
        ([rev(1), rev(2)], None, "HEAD", [(1, "up"), (2, "up")]),
        ([rev(1), rev(2)], "1", None, [(1, "down")]),
        ([rev(1), rev(2)], "1", "1", None),
        ([rev(1), rev(2)], "1", "2", [(2, "up")]),
        ([rev(1), rev(2)], "1", "HEAD", [(2, "up")]),
        ([rev(1), rev(2)], "2", None, [(2, "down"), (1, "down")]),
        ([rev(1), rev(2)], "2", "1", [(2, "down")]),
        ([rev(1), rev(2)], "2", "2", None),
        ([rev(1), rev(2)], "2", "HEAD", None),

        ([rev(1), rev(2), rev(3), rev(4)], None, None, None),
        ([rev(1), rev(2), rev(3), rev(4)], None, "1", [(1, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], None, "2", [(1, "up"), (2, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], None, "3", [(1, "up"), (2, "up"), (3, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], None, "4", [(1, "up"), (2, "up"), (3, "up"), (4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], None, "HEAD", [(1, "up"), (2, "up"), (3, "up"), (4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "1", None, [(1, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "1", "1", None),
        ([rev(1), rev(2), rev(3), rev(4)], "1", "2", [(2, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "1", "3", [(2, "up"), (3, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "1", "4", [(2, "up"), (3, "up"), (4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "1", "HEAD", [(2, "up"), (3, "up"), (4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "3", None, [(3, "down"), (2, "down"), (1, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "3", "1", [(3, "down"), (2, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "3", "2", [(3, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "3", "3", None),
        ([rev(1), rev(2), rev(3), rev(4)], "3", "4", [(4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "3", "HEAD", [(4, "up")]),
        ([rev(1), rev(2), rev(3), rev(4)], "4", None, [(4, "down"), (3, "down"), (2, "down"), (1, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "4", "1", [(4, "down"), (3, "down"), (2, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "4", "2", [(4, "down"), (3, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "4", "3", [(4, "down")]),
        ([rev(1), rev(2), rev(3), rev(4)], "4", "4", None),
        ([rev(1), rev(2), rev(3), rev(4)], "4", "HEAD", None),
    ]
)
def test_upgrade(
    revisions: Sequence[Revision],
    current: Optional[str],
    target: Optional[str],
    expected_path: List[Tuple[int, Direction]]
) -> None:
    maybe_path = find_migration_path(current, target, revisions)
    if expected_path is None:
        assert maybe_path is None
        return
    assert maybe_path is not None
    direction, path = maybe_path
    assert direction == {o for _, o in expected_path}.pop()
    assert extract_path(path) == [Op(r, o) for r, o in expected_path]
