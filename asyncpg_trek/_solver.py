from collections import defaultdict, deque
from itertools import tee
from typing import (
    Collection,
    Deque,
    Dict,
    Iterable,
    List,
    Mapping,
    Sequence,
    Tuple,
    TypeVar,
)

from asyncpg_trek._types import Direction, Migration, Revision

T = TypeVar("T")


def pairwise(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    # https://docs.python.org/3/library/itertools.html#itertools.pairwise
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def shortest_path(graph: Mapping[T, Sequence[T]], start: T, end: T) -> Sequence[T]:
    queue: Deque[List[T]] = deque()
    queue.append([start])
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == end:
            return path
        for adjacent in graph.get(node, ()):
            new_path = path.copy()
            new_path.append(adjacent)
            queue.append(new_path)
    raise LookupError


def find_migration_path(
    current: Revision,
    target: Revision,
    direction: Direction,
    migrations: Collection[Migration[T]],
) -> Sequence[Migration[T]]:
    migrations = [m for m in migrations if m.direction == direction]
    edges: Dict[Tuple[Revision, Revision], Migration[T]] = {}
    for migration in migrations:
        key = (migration.from_rev, migration.to_rev)
        if key in edges:
            raise RuntimeError(
                "Duplicate migration"
                f" {migration.from_rev} -> {migration.from_rev} found!"
            )
        edges[(migration.from_rev, migration.to_rev)] = migration

    rev_graph: Dict[Revision, List[Revision]] = defaultdict(list)
    for frm, to in edges.keys():
        rev_graph[frm].append(to)
    try:
        path = shortest_path(rev_graph, current, target)
    except LookupError:
        raise LookupError(f"No path found from {current} to rev {target} found")
    return [edges[(frm, to)] for frm, to in pairwise(path)]
