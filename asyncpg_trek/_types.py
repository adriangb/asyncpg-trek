import enum
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Literal, TypeVar

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
