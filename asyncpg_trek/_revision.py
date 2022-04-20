from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")

Operation = Callable[[T], Awaitable[None]]


@dataclass
class Revision(Generic[T]):
    revision: str
    upgrade: Optional[Operation[T]] = None
    downgrade: Optional[Operation[T]] = None
