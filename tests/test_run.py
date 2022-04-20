from pathlib import Path
from typing import Dict, Generator, List, Optional, Sequence, Union

import pytest

from asyncpg_trek import run
from tests.backend import InMemoryBackend

# convenience map of revisions to integers
revisions = {
    None: None,
    1: "2022_04_10_12_34_00_mig1",
    2: "2022_04_11_12_34_00_mig2",
    3: "2022_04_12_12_34_00_mig3",
    4: "2022_04_13_12_34_00_mig4",
    5: "2022_04_14_12_34_00_mig5",
}

# graph of all of the possible transitions from a given revision
Node = Union[int, None]
Graph = Dict[Node, List[Node]]
graph: Graph = {
    None: [None, 1, 2, 3, 4, 5],
    1: [None, 1, 2, 3, 4, 5],
    2: [3, 4, 5],
    3: [2, 3, 4, 5],
    4: [4, 5],
    5: [4, 5],
}


def find_paths(
    graph: Graph, max_depth: int = 12, path: Sequence[Node] = ()
) -> Generator[Sequence[Node], None, None]:
    assert max_depth > 0  # guard against infinite recursion
    if not path:
        for node in graph:
            yield from find_paths(graph, max_depth - 1, [node])
    else:
        cur = path[-1]
        for nxt in graph[cur]:
            if nxt in path:
                # cycle
                yield path
                continue
            yield from find_paths(graph, max_depth - 1, [*path, nxt])


@pytest.mark.asyncio
@pytest.mark.parametrize("targets", find_paths(graph))
async def test_valid_migrations(
    targets: Sequence[Optional[int]],
) -> None:
    """Test all possible migrations paths"""
    directory = Path(__file__).parent / "sqlite_revisions"
    backend = InMemoryBackend()
    for target in targets:
        target_revision = revisions[target]
        await run(backend=backend, directory=directory, target_revision=target_revision)
