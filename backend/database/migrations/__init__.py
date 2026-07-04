"""
Database Migrations for MetaPilot AI

This directory contains database migration scripts.
Use Alembic for database migrations.

To create a new migration:
1. Install Alembic: pip install alembic
2. Initialize (if not done): alembic init alembic
3. Configure alembic.ini with your database URL
4. Create migration: alembic revision --autogenerate -m "description"
5. Apply migration: alembic upgrade head

To apply all migrations:
    alembic upgrade head

To rollback:
    alembic downgrade -1
"""