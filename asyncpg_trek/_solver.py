from dataclasses import dataclass
from itertools import tee
from typing import Generic, Iterable, List, Optional, Sequence, Tuple, TypeVar

from asyncpg_trek._revision import Operation, Revision
from asyncpg_trek._typing import Literal

T = TypeVar("T")


class NoSolutionError(Exception):
    pass


@dataclass
class MigrationNode(Generic[T]):
    from_revision: Optional[Revision[T]]
    to_revision: Optional[Revision[T]]
    operation: Operation[T]


def pairwise(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    # https://docs.python.org/3/library/itertools.html#itertools.pairwise
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def check_upgrade(
    current: Optional[Revision[T]], *revisions: Revision[T]
) -> Sequence[MigrationNode[T]]:
    res: "List[MigrationNode[T]]" = []
    for cur, nxt in pairwise((current, *revisions)):
        assert nxt is not None
        if cur is None:
            if nxt.upgrade is None:
                raise NoSolutionError(
                    f"Cannot upgrade to {nxt.revision}"
                    f" because {nxt.revision} has no upgrade path"
                )
            res.append(MigrationNode(None, nxt, nxt.upgrade))
            continue
        if nxt.upgrade is None:
            raise NoSolutionError(
                f"Cannot upgrade to {nxt.revision}"
                f" because {nxt.revision} has no upgrade path"
            )
        res.append(MigrationNode(cur, nxt, nxt.upgrade))
    return res


def check_downgrade(
    current: Revision[T], *revisions: Optional[Revision[T]]
) -> Sequence[MigrationNode[T]]:
    res: "List[MigrationNode[T]]" = []
    for cur, nxt in pairwise((current, *revisions)):
        assert cur is not None
        if nxt is None:
            if cur.downgrade is None:
                raise NoSolutionError(
                    f"Cannot downgrade from {cur.revision}"
                    f" because {cur.revision} has no downgrade path"
                )
            res.append(MigrationNode(cur, nxt, cur.downgrade))
            return res
        if cur.downgrade is None:
            raise NoSolutionError(
                f"Cannot downgrade from {cur.revision}"
                f" because {cur.revision} has no downgrade path"
            )
        res.append(MigrationNode(cur, nxt, cur.downgrade))
    return res


Direction = Literal["up", "down"]


def find_migration_path(
    current: Optional[str], target: Optional[str], revisions: Sequence[Revision[T]]
) -> Optional[Tuple[Direction, Sequence[MigrationNode[T]]]]:
    if len(revisions) == 0:
        if not (current is None and target is None):
            raise NoSolutionError
        return None

    revision_ids = [rev.revision for rev in revisions]
    known_revision_ids = set(revision_ids)

    if target is None:
        if current is None:
            return None
        return "down", check_downgrade(
            *revisions[revision_ids.index(current) :: -1], None
        )
    elif target == "HEAD":
        target = revisions[-1].revision
    elif target not in known_revision_ids:
        raise ValueError(f"Unknown target revision {target}")

    res: "List[Revision[T]]" = []

    if current is None:
        for rev in revisions:
            res.append(rev)
            if rev.revision == target:
                break
        return "up", check_upgrade(None, *res)
    elif current not in known_revision_ids:
        raise ValueError(f"Unknown current revision {current}")

    if current == target:
        return None

    idx_current, idx_target = revision_ids.index(current), revision_ids.index(target)
    if idx_current < idx_target:
        return "up", check_upgrade(
            *revisions[idx_current:idx_target], revisions[idx_target]
        )
    return "down", check_downgrade(
        revisions[idx_current], *reversed(revisions[idx_target:idx_current])
    )
