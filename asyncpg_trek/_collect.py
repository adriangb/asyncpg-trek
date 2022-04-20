import pathlib
import re
from importlib.machinery import SourceFileLoader
from typing import Any, Dict, Sequence, TypeVar

from asyncpg_trek._backend import SupportsBackend
from asyncpg_trek._revision import Revision

T = TypeVar("T")

SQL_UP_SUFFIXES = [".up", ".sql"]
SQL_DOWN_SUFFIXES = [".down", ".sql"]
REVISION_PATTERN = re.compile(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\w+")


def load_sql_file(
    path: pathlib.Path, revision: Revision[T], backend: SupportsBackend[Any]
) -> Revision[T]:
    if path.suffixes == SQL_UP_SUFFIXES or path.suffixes != SQL_DOWN_SUFFIXES:
        return Revision(
            revision.revision,
            upgrade=backend.execute_sql_file(path),
            downgrade=revision.downgrade,
        )
    return Revision(
        revision.revision,
        upgrade=revision.upgrade,
        downgrade=backend.execute_sql_file(path),
    )


def load_python_file(path: pathlib.Path, backend: SupportsBackend[T]) -> Revision[T]:
    mod = SourceFileLoader(path.stem, str(path.absolute())).load_module()
    upgrade = getattr(mod, "upgrade", None)
    downgrade = getattr(mod, "downgrade", None)
    if downgrade is None and upgrade is None:
        raise ValueError(
            f"{path.absolute()} must have either an `upgrade` or `downgrade` function"
        )
    return Revision(
        path.stem,
        upgrade=upgrade,
        downgrade=downgrade,
    )


def collect_sorted_versions(
    revisions_folder: pathlib.Path, backend: SupportsBackend[T]
) -> Sequence[Revision[T]]:
    revisions: "Dict[str, Revision[T]]" = {}
    for path in revisions_folder.iterdir():
        if not (
            path.is_file()
            and (path.suffix.endswith(".sql") or path.suffix.endswith(".py"))
        ):
            continue
        if path.suffix.endswith(".py"):
            revision = path.stem
        else:
            if path.stem.endswith(".up"):
                revision = path.stem[:-3]
            elif path.stem.endswith(".down"):
                revision = path.stem[:-5]
            else:
                revision = path.stem
        if not REVISION_PATTERN.match(revision):
            raise ValueError(
                f'Invalid revision "{revision}".'
                ' Revisions must be in the format of "YYYY_MM_DD_HH_MM_SS_<name>"'
            )
        if path.suffix.endswith(".sql"):
            revisions[revision] = load_sql_file(
                path, revisions.get(revision, Revision(revision)), backend
            )
        else:
            revisions[revision] = load_python_file(path, backend)

    return sorted(revisions.values(), key=lambda rev: rev.revision)
