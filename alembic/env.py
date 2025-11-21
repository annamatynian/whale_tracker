"""
Alembic Environment Configuration for Whale Tracker

This module configures Alembic to work with our modular database architecture.
Supports both online (asyncio) and offline migration modes.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import models and config
from models.database import Base
from config.settings import get_settings
from models.db_connection import DatabaseConfig

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from settings.

    This allows us to use the same configuration system
    as the rest of the application.
    """
    try:
        settings = get_settings()

        # Build DatabaseConfig from settings
        db_config = DatabaseConfig(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )

        # For migrations, use synchronous URL
        return db_config.get_sync_url()

    except Exception as e:
        print(f"Error getting database URL: {e}")
        # Fallback to environment variable if settings fail
        return os.getenv(
            'DATABASE_URL',
            'sqlite:///data/database/whale_tracker.db'
        )


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with provided connection.

    Args:
        connection: SQLAlchemy connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get URL and build async configuration
    url = get_url()

    # Replace postgresql:// with postgresql+asyncpg:// for async
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+asyncpg://')

    # Create async engine
    configuration = {
        'sqlalchemy.url': url,
        'sqlalchemy.poolclass': pool.NullPool,
    }

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Wrapper that handles async execution.
    """
    asyncio.run(run_async_migrations())


# Determine mode and run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
