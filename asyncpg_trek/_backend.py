import pathlib
from typing import AsyncContextManager, Awaitable, Callable, Optional, TypeVar

from asyncpg_trek._typing import Protocol

T = TypeVar("T")


class SupportsBackend(Protocol[T]):
    def connect(self) -> AsyncContextManager[T]:
        ...

    async def create_table_idempotent(self, connection: T) -> None:
        ...

    async def get_current_revision(self, connection: T) -> Optional[str]:
        ...

    async def record_migration(
        self, connection: T, *, from_revision: Optional[str], to_revision: Optional[str]
    ) -> None:
        ...

    def execute_sql_file(self, path: pathlib.Path) -> Callable[[T], Awaitable[None]]:
        ...
