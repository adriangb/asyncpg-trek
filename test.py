import asyncio
import logging
logging.basicConfig(level="INFO")
from pathlib import Path
import asyncpg

from asyncpg_trek.run import run


async def main() -> None:
    async with asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
    ) as pool:
        conn: asyncpg.Connection
        async with pool.acquire() as conn:
            await run(
                conn=conn,
                directory=Path(__file__).parent / "tests" / "revisions_1",
                target_revision="2022_04_13_12_34_00_mig4"
            )

if __name__ == "__main__":
    asyncio.run(main())
