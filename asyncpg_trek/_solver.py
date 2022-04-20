from typing import Literal, NamedTuple, Optional, Sequence, List, Tuple

from asyncpg_trek._revision import Revision, Operation


class NoSolutionError(Exception):
    pass


class MigrationNode(NamedTuple):
    revision: Revision
    operation: Operation


def check_upgrade(revisions: Sequence[Revision]) -> Sequence[MigrationNode]:
    res: "List[MigrationNode]" = []
    if len(revisions) == 1:
        first = last = next(iter(revisions))
    else:
        first, *_, last = revisions
    for rev in revisions:
        if rev.upgrade is None:
            raise NoSolutionError(
                f"Migration from {first.revision} to {last.revision} is not possible because"
                f" version {rev.revision} has no upgrade path"
            )
        res.append(MigrationNode(rev, rev.upgrade))
    return res


def check_downgrade(revisions: Sequence[Revision]) -> Sequence[MigrationNode]:
    res: "List[MigrationNode]" = []
    if len(revisions) == 1:
        first = last = next(iter(revisions))
    else:
        first, *_, last = revisions
    for rev in revisions:
        if rev.downgrade is None:
            raise NoSolutionError(
                f"Migration from {first.revision} to {last.revision} is not possible because"
                f" version {rev.revision} has no downgrade path"
            )
        res.append(MigrationNode(rev, rev.downgrade))
    return res


Direction = Literal["up", "down"]


def find_migration_path(current: Optional[str], target: Optional[str], revisions: Sequence[Revision]) -> Optional[Tuple[Direction, Sequence[MigrationNode]]]:
    if len(revisions) == 0:
        if not (current is None and target is None):
            raise NoSolutionError
        return None

    revision_ids = [rev.revision for rev in revisions]
    known_revision_ids = set(revision_ids)

    if target is None:
        if current is None:
            return None
        return "down", check_downgrade(revisions[revision_ids.index(current)::-1])
    elif target == "HEAD":
        target = revisions[-1].revision
    elif target not in known_revision_ids:
        raise ValueError(f"Unknown target revision {target}")        

    res: "List[Revision]" = []

    if current is None:
        for rev in revisions:
            res.append(rev)
            if rev.revision == target:
                break
        path = check_upgrade(res)
        if not path:
            return None
        return "up", path
    elif current not in known_revision_ids:
        raise ValueError(f"Unknown current revision {current}")     

    if current == target:
        return None

    idx_current, idx_target = revision_ids.index(current), revision_ids.index(target)
    if idx_current < idx_target:
        path = check_upgrade(revisions[idx_current+1:idx_target+1])
        if not path:
            return None
        return "up", path
    path = check_downgrade(revisions[idx_current:idx_target:-1])
    if not path:
        return None
    return "down", path
