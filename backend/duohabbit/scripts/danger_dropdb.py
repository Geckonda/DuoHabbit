"""
Dangerous script to drop all database tables and content.
This leaves the database empty so the app can recreate it on startup.
⚠️  WARNING: This will delete ALL data in the database! ⚠️
Only use this for development database iterations.
"""

import asyncio
import sys

from sqlalchemy import text

from duohabbit.db import engine


async def drop_all_tables() -> None:
    """Drop all database tables and content."""
    print("⚠️  WARNING: This will drop ALL database tables and content!")
    print("This action cannot be undone.")
    print()

    if len(sys.argv) < 2 or sys.argv[1] != "--yes-i-am-sure":
        print("To proceed, run:")
        print("  uv run python -m sparkup.scripts.danger_dropdb --yes-i-am-sure")
        sys.exit(1)

    print("Dropping all database tables (including stale/orphaned tables)...")

    try:
        async with engine().begin() as conn:
            # First, drop all tables in the public schema
            # This uses CASCADE to handle foreign key dependencies
            result = await conn.execute(
                text(
                    """
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """
                )
            )
            tables = [row[0] for row in result]

            if tables:
                print(f"Found {len(tables)} table(s) to drop: {', '.join(tables)}")
                # Quote table names to handle reserved keywords like 'user'
                quoted_tables = ", ".join(f'"{table}"' for table in tables)
                await conn.execute(
                    text(f"DROP TABLE IF EXISTS {quoted_tables} CASCADE")
                )
            else:
                print("No tables found in the database.")

            # Also drop all sequences (used for auto-increment columns)
            result = await conn.execute(
                text(
                    """
                    SELECT sequencename 
                    FROM pg_sequences 
                    WHERE schemaname = 'public'
                """
                )
            )
            sequences = [row[0] for row in result]

            if sequences:
                print(
                    f"Found {len(sequences)} sequence(s) to drop: {', '.join(sequences)}"
                )
                for seq in sequences:
                    # Quote sequence names to handle reserved keywords
                    await conn.execute(text(f'DROP SEQUENCE IF EXISTS "{seq}" CASCADE'))

        print("✓ All database tables and sequences have been dropped successfully!")
        print()
        print("The database is now empty. Start the app to recreate the schema.")

    # Caught for reporting and this is a dev script anyway.
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"✗ Error dropping database tables: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(drop_all_tables())
