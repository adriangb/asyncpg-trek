import pathlib
from importlib.machinery import SourceFileLoader
import re
from typing import Dict, Sequence

import asyncpg  # type: ignore[import]

from asyncpg_trek._revision import Revision


SQL_UP_SUFFIXES = [".up", ".sql"]
SQL_DOWN_SUFFIXES = [".down", ".sql"]
REVISION_PATTERN = re.compile(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_\w+")


def load_sql_file(path: pathlib.Path, revision: Revision) -> Revision:

    async def run(connection: asyncpg.Connection) -> None:
        with open(path) as f:
            await connection.execute(f.read())  # type: ignore

    if path.suffixes == SQL_UP_SUFFIXES or path.suffixes != SQL_DOWN_SUFFIXES:
        return revision._replace(upgrade=run)
    return revision._replace(downgrade=run)


def load_python_file(path: pathlib.Path) -> Revision:
    mod = SourceFileLoader(path.stem, str(path.absolute())).load_module()
    upgrade = getattr(mod, "upgrade", None)
    downgrade = getattr(mod, "downgrade", None)
    if downgrade is None and upgrade is None:
        raise ValueError(
            f"{path.absolute()} must have either an `upgrade` or `downgrade` function"
        )
    return Revision(path.stem, upgrade=upgrade, downgrade=downgrade)


def collect_sorted_versions(revisions_folder: pathlib.Path) -> Sequence[Revision]:
    revisions: "Dict[str, Revision]" = {}
    for path in revisions_folder.iterdir():
        if not (path.is_file() and (path.suffix.endswith(".sql") or path.suffix.endswith(".py"))):
            continue
        if path.suffix.endswith(".py"):
            revision = path.stem
        else:
            revision = path.stem.removesuffix(".up").removesuffix(".down")
        if not REVISION_PATTERN.match(revision):
            raise ValueError(
                f"Invalid revision \"{revision}\"."
                " Revisions must be in the format of \"YYYY_MM_DD_HH_MM_SS-<name>\""
            )
        if path.suffix.endswith(".sql"):
            revisions[revision] = load_sql_file(path, revisions.get(revision, Revision(revision)))
        else:
            revisions[revision] = load_python_file(path)

    return sorted(revisions.values(), key=lambda rev: rev.revision)
