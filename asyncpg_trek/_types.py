import enum
import sys
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


T = TypeVar("T")


Operation = Callable[[T], Awaitable[None]]


Revision = str
INITIAL_REVISION: Literal["initial"] = "initial"


class Direction(enum.Enum):
    up = enum.auto()
    down = enum.auto()


@dataclass(frozen=True)
class Migration(Generic[T]):
    operation: Operation[T]
    from_rev: Revision
    to_rev: Revision
    direction: Direction
