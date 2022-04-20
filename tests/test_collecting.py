from dataclasses import dataclass
import pathlib
from typing import Sequence

from asyncpg_trek._collect import collect_sorted_versions
from asyncpg_trek._revision import Revision


@dataclass
class SimpleRevision:
    revision: str
    has_up: bool
    has_down: bool


def simplify_revisions(revs: Sequence[Revision]) -> Sequence[SimpleRevision]:
    return [
        SimpleRevision(r.revision, r.upgrade is not None, r.downgrade is not None)
        for r in revs
    ]


def test_collect() -> None:
    revs = collect_sorted_versions(pathlib.Path(__file__).parent / "revisions_1")
    expected = [
        SimpleRevision("2022_04_10_12_34_00_mig1", True, True),
        SimpleRevision("2022_04_11_12_34_00_mig2", True, False),
        SimpleRevision("2022_04_12_12_34_00_mig3", True, True),
        SimpleRevision("2022_04_13_12_34_00_mig4", True, False),
        SimpleRevision("2022_04_14_12_34_00_mig5", True, True),
    ]
    assert simplify_revisions(revs) == expected
