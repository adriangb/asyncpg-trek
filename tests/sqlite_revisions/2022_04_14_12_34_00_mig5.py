import sqlite3


async def upgrade(conn: sqlite3.Connection) -> None:
    total = conn.total_changes
    conn.execute(
        "UPDATE people SET nickname = 'Darth Vader' WHERE name = 'Anakin Skywalker'"
    )
    assert conn.total_changes == total + 1


async def downgrade(conn: sqlite3.Connection) -> None:
    total = conn.total_changes
    conn.execute("UPDATE people SET nickname = 'Ani' WHERE name = 'Anakin Skywalker'")
    assert conn.total_changes == total + 1
