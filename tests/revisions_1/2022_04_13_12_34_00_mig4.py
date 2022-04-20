from pathlib import Path
from typing import AsyncIterator
import asyncpg  # type: ignore[import]


async def upgrade(conn: asyncpg.Connection) -> None:
    async def stream() -> "AsyncIterator[bytes]":
        with open(Path(__file__).parent / "names.txt", "rb") as f:
            for line in f.readlines():
                yield line + b"\n"

    await conn.copy_to_table("test", source=stream(), columns=["name"])  # type: ignore
