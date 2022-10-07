from dataclasses import dataclass
from typing import List, Sequence

import pytest

from asyncpg_trek._solver import find_migration_path
from asyncpg_trek._types import Direction, Migration

Mig = Migration[None]


@dataclass
class OperationStub:
    from_rev: int
    to_rev: int

    @property
    def id(self) -> str:
        return f"{self.from_rev}->{self.to_rev}"

    async def __call__(self, connection: None) -> None:
        ...


def make_mig(from_rev: int, to_rev: int, dir: Direction) -> Mig:
    op = OperationStub(from_rev, to_rev)
    return Migration(op, str(from_rev), str(to_rev), dir)


def extract_path(got: Sequence[Mig]) -> List[str]:
    res: List[str] = []
    for node in got:
        assert isinstance(node.operation, OperationStub)
        res.append(node.operation.id)
    return res


cyclic_graph = [
    make_mig(0, 1, Direction.up),
    make_mig(1, 0, Direction.up),
    make_mig(1, 0, Direction.down),
]

simple_graph = [
    make_mig(0, 1, Direction.up),
    make_mig(1, 0, Direction.down),
    make_mig(1, 2, Direction.up),
    make_mig(2, 1, Direction.down),
    make_mig(1, 3, Direction.up),
    make_mig(3, 2, Direction.down),
    make_mig(2, 4, Direction.up),
    make_mig(4, 2, Direction.down),
]


@pytest.mark.parametrize(
    "migrations,current,target,expected_path",
    [
        (simple_graph, 0, 0, []),
        (simple_graph, 0, 1, ["0->1"]),
        (simple_graph, 0, 2, ["0->1", "1->2"]),
        (simple_graph, 0, 3, ["0->1", "1->3"]),
        (simple_graph, 0, 4, ["0->1", "1->2", "2->4"]),
        (simple_graph, 1, 1, []),
        (simple_graph, 1, 2, ["1->2"]),
        (simple_graph, 1, 3, ["1->3"]),
        (simple_graph, 1, 4, ["1->2", "2->4"]),
        (simple_graph, 2, 2, []),
        # 2 -> 3 is not possible!
        (simple_graph, 2, 4, ["2->4"]),
        (simple_graph, 4, 4, []),
        (cyclic_graph, 0, 1, ["0->1"]),
        (cyclic_graph, 1, 0, ["1->0"]),
    ],
)
def test_find_single_path_up(
    migrations: Sequence[Mig],
    current: int,
    target: int,
    expected_path: List[str],
) -> None:
    plan = find_migration_path(
        str(current), str(target), direction=Direction.up, migrations=migrations
    )
    path = extract_path(plan)
    assert path == expected_path


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        (simple_graph, 100, 1),
    ],
)
def test_find_path_current_does_not_exist(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.up, migrations=migrations
        )


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        (simple_graph, 0, 100),
    ],
)
def test_find_path_target_does_not_exist(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.up, migrations=migrations
        )


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        (simple_graph, 2, 3),
    ],
)
def test_find_single_path_up_no_solution(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.up, migrations=migrations
        )


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        (simple_graph, 2, 3),
    ],
)
def test_cycles(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.up, migrations=migrations
        )


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        ([], 0, 1),
    ],
)
def test_empty_migrations(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.up, migrations=migrations
        )


@pytest.mark.parametrize(
    "migrations,current,target,expected_path",
    [
        (simple_graph, 0, 0, []),
        (simple_graph, 1, 0, ["1->0"]),
        (simple_graph, 2, 0, ["2->1", "1->0"]),
        (simple_graph, 3, 0, ["3->2", "2->1", "1->0"]),
        (simple_graph, 4, 0, ["4->2", "2->1", "1->0"]),
        (simple_graph, 1, 1, []),
        (simple_graph, 2, 1, ["2->1"]),
        (simple_graph, 3, 1, ["3->2", "2->1"]),
        (simple_graph, 4, 1, ["4->2", "2->1"]),
        (simple_graph, 2, 2, []),
        (simple_graph, 3, 2, ["3->2"]),
        (simple_graph, 4, 2, ["4->2"]),
        (simple_graph, 4, 4, []),
        (cyclic_graph, 1, 0, ["1->0"]),
    ],
)
def test_find_single_path_down(
    migrations: Sequence[Mig],
    current: int,
    target: int,
    expected_path: List[str],
) -> None:
    plan = find_migration_path(
        str(current), str(target), direction=Direction.down, migrations=migrations
    )
    path = extract_path(plan)
    assert path == expected_path


@pytest.mark.parametrize(
    "migrations,current,target",
    [
        (cyclic_graph, 0, 1),
    ],
)
def test_find_path_down_not_found(
    migrations: Sequence[Mig],
    current: int,
    target: int,
) -> None:
    with pytest.raises(LookupError):
        find_migration_path(
            str(current), str(target), direction=Direction.down, migrations=migrations
        )
