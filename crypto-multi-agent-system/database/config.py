"""
Database Configuration for Crypto Multi-Agent System
Supports easy switching between SQLite and PostgreSQL
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_DIR = PROJECT_ROOT / "data" / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite or postgresql

if DATABASE_TYPE == "sqlite":
    DATABASE_PATH = DATABASE_DIR / "crypto_analysis.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    ENGINE_KWARGS = {
        "echo": os.getenv("DATABASE_DEBUG", "false").lower() == "true",
        # SQLite specific optimizations
        "pool_pre_ping": True,
        "connect_args": {
            "check_same_thread": False,  # Allow multithreading
            "timeout": 20,  # Connection timeout
        }
    }
elif DATABASE_TYPE == "postgresql":
    # PostgreSQL configuration from environment variables
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "crypto_analysis")
    DB_USER = os.getenv("DB_USER", "crypto_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    ENGINE_KWARGS = {
        "echo": os.getenv("DATABASE_DEBUG", "false").lower() == "true",
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # Recycle connections every hour
    }
else:
    raise ValueError(f"Unsupported database type: {DATABASE_TYPE}")

# Create engine
engine = create_engine(DATABASE_URL, **ENGINE_KWARGS)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_session():
    """
    Get database session for dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    print(f"Creating database tables...")
    print(f"Database URL: {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    print("WARNING: Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


def get_database_info():
    """
    Get information about the database configuration
    """
    return {
        "database_type": DATABASE_TYPE,
        "database_url": DATABASE_URL.replace(DB_PASSWORD, "***") if DATABASE_TYPE == "postgresql" else DATABASE_URL,
        "tables_count": len(Base.metadata.tables),
        "table_names": list(Base.metadata.tables.keys())
    }
