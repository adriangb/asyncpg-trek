import pathlib
from dataclasses import dataclass
from typing import Any, Sequence

import pytest

from asyncpg_trek._collect import collect_sorted_versions
from asyncpg_trek._revision import Revision
from tests.backend import InMemoryBackend


@dataclass
class SimpleRevision:
    revision: str
    has_up: bool
    has_down: bool


def simplify_revisions(revs: Sequence[Revision[Any]]) -> Sequence[SimpleRevision]:
    return [
        SimpleRevision(r.revision, r.upgrade is not None, r.downgrade is not None)
        for r in revs
    ]


def test_collect() -> None:
    backend = InMemoryBackend()
    revs = collect_sorted_versions(
        pathlib.Path(__file__).parent / "sqlite_revisions", backend
    )
    expected = [
        SimpleRevision("2022_04_10_12_34_00_mig1", True, True),
        SimpleRevision("2022_04_11_12_34_00_mig2", True, False),
        SimpleRevision("2022_04_12_12_34_00_mig3", True, True),
        SimpleRevision("2022_04_13_12_34_00_mig4", True, False),
        SimpleRevision("2022_04_14_12_34_00_mig5", True, True),
    ]
    assert simplify_revisions(revs) == expected


def test_collect_non_migration_files_are_ignored() -> None:
    backend = InMemoryBackend()
    revs = collect_sorted_versions(
        pathlib.Path(__file__).parent / "revisions_with_non_migration_files", backend
    )
    assert [rev.revision for rev in revs] == ["2022_04_10_12_34_00_mig1"]


def test_collect_python_file_without_upgrade_or_downgrade() -> None:
    backend = InMemoryBackend()
    with pytest.raises(
        ValueError, match="must have either an `upgrade` or `downgrade` function"
    ):
        collect_sorted_versions(
            pathlib.Path(__file__).parent
            / "revisions_python_file_without_upgrade_or_downgrade",
            backend,
        )


def test_collect_filename_pattern_does_not_match() -> None:
    backend = InMemoryBackend()
    with pytest.raises(
        ValueError,
        match='Revisions must be in the format of "YYYY_MM_DD_HH_MM_SS_<name>"',
    ):
        collect_sorted_versions(
            pathlib.Path(__file__).parent / "revisions_invalid_filename_pattern",
            backend,
        )


def test_collect_no_revisions() -> None:
    backend = InMemoryBackend()
    assert (
        collect_sorted_versions(
            pathlib.Path(__file__).parent / "revisions_no_revisions", backend
        )
        == []
    )
