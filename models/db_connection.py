"""
Database Connection Manager

Modular, abstracted database connection handling for PostgreSQL.
Supports both sync and async operations.
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine, Engine, event, pool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker, Session

from models.database import Base


class DatabaseConfig:
    """
    Database configuration abstraction.

    Decouples database config from connection logic.
    """

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5432,
        database: str = 'whale_tracker',
        user: str = 'postgres',
        password: str = '',
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False
    ):
        """
        Initialize database configuration.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Echo SQL queries (for debugging)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

    def get_sync_url(self) -> str:
        """Get synchronous database URL"""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def get_async_url(self) -> str:
        """Get asynchronous database URL"""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    @classmethod
    def from_env(cls, settings) -> 'DatabaseConfig':
        """
        Create config from environment settings.

        Args:
            settings: Settings object from config/settings.py

        Returns:
            DatabaseConfig instance
        """
        return cls(
            host=getattr(settings, 'DB_HOST', 'localhost'),
            port=getattr(settings, 'DB_PORT', 5432),
            database=getattr(settings, 'DB_NAME', 'whale_tracker'),
            user=getattr(settings, 'DB_USER', 'postgres'),
            password=getattr(settings, 'DB_PASSWORD', ''),
            pool_size=getattr(settings, 'DB_POOL_SIZE', 5),
            max_overflow=getattr(settings, 'DB_MAX_OVERFLOW', 10),
            echo=getattr(settings, 'DB_ECHO', False)
        )


class DatabaseManager:
    """
    Database connection manager (synchronous).

    Handles sync database operations for batch processing, migrations, etc.
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database manager.

        Args:
            config: DatabaseConfig instance
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def init_engine(self) -> Engine:
        """
        Initialize synchronous engine.

        Returns:
            SQLAlchemy Engine
        """
        if self._engine is None:
            self.logger.info(f"Initializing sync engine: {self.config.database}")

            self._engine = create_engine(
                self.config.get_sync_url(),
                poolclass=pool.QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                echo=self.config.echo,
                pool_pre_ping=True  # Verify connections before using
            )

            # Setup connection event listeners
            @event.listens_for(self._engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                self.logger.debug("Database connection established")

            @event.listens_for(self._engine, "close")
            def receive_close(dbapi_conn, connection_record):
                self.logger.debug("Database connection closed")

        return self._engine

    def init_session_factory(self) -> sessionmaker:
        """
        Initialize session factory.

        Returns:
            SQLAlchemy sessionmaker
        """
        if self._session_factory is None:
            engine = self.init_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

        return self._session_factory

    @contextmanager
    def session(self):
        """
        Context manager for database sessions.

        Usage:
            with db_manager.session() as session:
                session.query(Model).all()

        Yields:
            SQLAlchemy Session
        """
        factory = self.init_session_factory()
        session = factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            self.logger.error(f"Session error: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self):
        """Create all database tables"""
        self.logger.info("Creating database tables...")
        engine = self.init_engine()
        Base.metadata.create_all(bind=engine)
        self.logger.info("Database tables created successfully")

    def drop_all_tables(self):
        """Drop all database tables (DESTRUCTIVE)"""
        self.logger.warning("Dropping all database tables...")
        engine = self.init_engine()
        Base.metadata.drop_all(bind=engine)
        self.logger.warning("All database tables dropped")

    def close(self):
        """Close database connections"""
        if self._engine:
            self.logger.info("Closing database connections...")
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


class AsyncDatabaseManager:
    """
    Async database connection manager.

    Handles async database operations for real-time monitoring.
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize async database manager.

        Args:
            config: DatabaseConfig instance
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    def init_engine(self) -> AsyncEngine:
        """
        Initialize asynchronous engine.

        Returns:
            SQLAlchemy AsyncEngine
        """
        if self._engine is None:
            self.logger.info(f"Initializing async engine: {self.config.database}")

            self._engine = create_async_engine(
                self.config.get_async_url(),
                poolclass=pool.AsyncAdaptedQueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                echo=self.config.echo,
                pool_pre_ping=True
            )

        return self._engine

    def init_session_factory(self) -> async_sessionmaker:
        """
        Initialize async session factory.

        Returns:
            SQLAlchemy async_sessionmaker
        """
        if self._session_factory is None:
            engine = self.init_engine()
            self._session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Usage:
            async with async_db_manager.session() as session:
                result = await session.execute(query)

        Yields:
            SQLAlchemy AsyncSession
        """
        factory = self.init_session_factory()
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                self.logger.error(f"Async session error: {e}", exc_info=True)
                await session.rollback()
                raise

    async def create_all_tables(self):
        """Create all database tables (async)"""
        self.logger.info("Creating database tables (async)...")
        engine = self.init_engine()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.logger.info("Database tables created successfully")

    async def drop_all_tables(self):
        """Drop all database tables (async, DESTRUCTIVE)"""
        self.logger.warning("Dropping all database tables (async)...")
        engine = self.init_engine()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        self.logger.warning("All database tables dropped")

    async def close(self):
        """Close async database connections"""
        if self._engine:
            self.logger.info("Closing async database connections...")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# ==================== Factory Functions ====================

def create_sync_db_manager(
    config: Optional[DatabaseConfig] = None,
    settings=None
) -> DatabaseManager:
    """
    Factory function for synchronous database manager.

    Args:
        config: DatabaseConfig instance (optional)
        settings: Settings object (optional, for env-based config)

    Returns:
        DatabaseManager instance
    """
    if config is None:
        if settings is not None:
            config = DatabaseConfig.from_env(settings)
        else:
            config = DatabaseConfig()

    return DatabaseManager(config)


def create_async_db_manager(
    config: Optional[DatabaseConfig] = None,
    settings=None
) -> AsyncDatabaseManager:
    """
    Factory function for asynchronous database manager.

    Args:
        config: DatabaseConfig instance (optional)
        settings: Settings object (optional, for env-based config)

    Returns:
        AsyncDatabaseManager instance
    """
    if config is None:
        if settings is not None:
            config = DatabaseConfig.from_env(settings)
        else:
            config = DatabaseConfig()

    return AsyncDatabaseManager(config)
