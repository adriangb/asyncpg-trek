from typing import Awaitable, Callable, NamedTuple, Optional

import asyncpg  # type: ignore[import]


Operation = Callable[[asyncpg.Connection], Awaitable[None]]


class Revision(NamedTuple):
    revision: str
    upgrade: Optional[Operation] = None
    downgrade: Optional[Operation] = None
