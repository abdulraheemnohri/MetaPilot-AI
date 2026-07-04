"""
Alembic Migrations for MetaPilot-AI Database

This directory contains database migration scripts managed by Alembic.
Run migrations using: alembic upgrade head
Create new migrations: alembic revision --autogenerate -m "message"
"""

from alembic import context
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

__all__ = ['run_migrations', 'get_current_revision']


def run_migrations(connection):
    """Run all pending migrations on the given connection."""
    context.configure(
        connection=connection,
        target_metadata=None,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def get_current_revision():
    """Get the current database revision."""
    script = ScriptDirectory.from_config(context.config)
    return script.get_current_head()