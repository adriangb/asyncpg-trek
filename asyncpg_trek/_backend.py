import pathlib
from typing import AsyncContextManager, Optional, TypeVar

from asyncpg_trek._types import Operation
from asyncpg_trek._typing import Protocol

T = TypeVar("T")


class SupportsBackend(Protocol[T]):
    connection: T

    def connect(self) -> AsyncContextManager[T]:
        ...

    async def create_table_idempotent(self) -> None:
        ...

    async def get_current_revision(self) -> Optional[str]:
        ...

    async def record_migration(
        self, *, from_revision: Optional[str], to_revision: Optional[str]
    ) -> None:
        ...

    def build_operation_from_sql_file(self, path: pathlib.Path) -> Operation:
        ...
