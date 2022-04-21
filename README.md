# asyncpg-trek: simple migrations for asyncpg

A simple library for managing migrations.

## Target audience

Me.
But maybe if you use [asyncpg] and prefer to write migrations as raw SQL (i.e. you're not using SQLAlchemy/Alembic) then you as well.

## Features

- **async**: migrations usually don't benefit from being async, but you benefit from using the same database driver in as your application uses (only [asyncpg] is supported).
- **simple**: you just create `.sql` or Python files in a folder of your choosing and point this tool at that folder. No need to fight a new API to write migrations in.
- **API centric**: there is no CLI to figure out, _you_ decide how migrations get called, _you_ control how the database connection gets created. This makes it trivial to run migrations in tests, wrap them in a CLI or run them via an exposed HTTP endpoint.
- **declarative**: just specify the version you want and the library figures out if it needs an upgrade, downgrade or no action.

## Example usage

```python
from pathlib import Path

import asyncpg
from asyncpg_trek import run
from asyncpg_trek.asyncpg import AsyncpgBackend

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

async def run_migrations(
    conn: asyncpg.Connection,
    target_revision: Optional[str] = None,
) -> None:
    backend = AsyncpgBackend(conn)
    await run(backend, MIGRATIONS_DIR, target_revision=target_revision)
```

You could make this an entrypoint in a docker image, an admin endpoint in your API or a helper function in your tests (or all of the above).
