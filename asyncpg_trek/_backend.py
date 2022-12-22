import pathlib
from typing import AsyncContextManager, Optional, TypeVar

from asyncpg_trek._types import Operation
from asyncpg_trek._typing import Protocol

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class SupportsBackendExecutor(Protocol[T_co]):
    async def create_table_idempotent(self) -> None:
        """Create the migrations table.

        This method should be a no-op if the table exists.
        """
        ...

    async def get_current_revision(self) -> Optional[str]:
        """Get the current revision from the database, returning None
        if this database has no migrations applied.
        """
        ...

    async def record_migration(
        self, from_revision: Optional[str], to_revision: Optional[str]
    ) -> None:
        """Record that we successfully executed a migration"""
        ...

    async def execute_operation(self, operation: Operation[T_co]) -> None:
        """Execute an operation"""
        ...


class SupportsBackend(Protocol[T]):
    def connect(self) -> AsyncContextManager[SupportsBackendExecutor[T]]:
        """Connect to the database and establish any necessary transactions or
        exception blocks to revert changes if migrations fail and return an object
        implementing the SupportsBackendExecutor protocol that will be used to execute
        migrations and record the state of the database.
        """
        ...

    def prepare_operation_from_sql_file(self, path: pathlib.Path) -> Operation[T]:
        """Create an operation from a SQL file.

        The operation will be passed to the `execute_operation` of SupportsBackendExecutor.
        """
        ...
