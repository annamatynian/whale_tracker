"""
Database initialization script for production deployment.
Run this once on server to create tables.
"""

import asyncio
import logging
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from models.database import Base
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database tables"""
    try:
        # Get DB URL from environment
        db_url = (
            f"postgresql+asyncpg://"
            f"{os.getenv('DB_USER', 'postgres')}:"
            f"{os.getenv('DB_PASSWORD')}@"
            f"{os.getenv('DB_HOST', 'localhost')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'whale_tracker')}"
        )
        
        logger.info("🗄️  Connecting to database...")
        logger.info(f"Host: {os.getenv('DB_HOST')}")
        logger.info(f"Database: {os.getenv('DB_NAME')}")
        
        engine = create_async_engine(db_url, echo=True)
        
        async with engine.begin() as conn:
            logger.info("📋 Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully!")
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("⚠️  python-dotenv not installed, using system env vars")
    
    asyncio.run(init_db())
