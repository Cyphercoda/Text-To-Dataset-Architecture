"""
Database configuration and session management
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base.metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Async engine for FastAPI
async_engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
    poolclass=QueuePool if not settings.is_testing else NullPool,
    pool_size=settings.DATABASE_POOL_SIZE if not settings.is_testing else 0,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if not settings.is_testing else 0,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.DEBUG,
    poolclass=QueuePool if not settings.is_testing else NullPool,
    pool_size=settings.DATABASE_POOL_SIZE if not settings.is_testing else 0,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if not settings.is_testing else 0,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)


# Database event listeners for monitoring
@event.listens_for(async_engine.sync_engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Event listener for new database connections"""
    logger.debug("New database connection established")


@event.listens_for(async_engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Event listener for connection checkout from pool"""
    logger.debug("Database connection checked out from pool")


@event.listens_for(async_engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Event listener for connection checkin to pool"""
    logger.debug("Database connection checked in to pool")


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self._async_engine = async_engine
        self._sync_engine = sync_engine
        self._initialized = False
    
    async def init_db(self) -> None:
        """Initialize database connection and tables"""
        if self._initialized:
            return
        
        try:
            # Test async connection
            async with self._async_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("✅ Database connection established successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def close_db(self) -> None:
        """Close database connections"""
        if not self._initialized:
            return
        
        try:
            await self._async_engine.dispose()
            self._sync_engine.dispose()
            logger.info("✅ Database connections closed")
            self._initialized = False
            
        except Exception as e:
            logger.error(f"❌ Error closing database connections: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized"""
        return self._initialized
    
    async def health_check(self) -> dict:
        """Perform database health check"""
        try:
            async with self._async_engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                await result.fetchone()
            
            # Get connection pool stats
            pool = self._async_engine.pool
            pool_stats = {
                "pool_size": pool.size(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "checked_in": pool.checkedin(),
            }
            
            return {
                "status": "healthy",
                "database": "connected",
                "pool_stats": pool_stats,
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            }


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session
    
    Usage:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """
    Get synchronous database session (for Celery tasks)
    
    Usage:
        with get_sync_db() as db:
            ...
    """
    return SessionLocal()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session
    
    Usage:
        async with get_db_context() as db:
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseTransaction:
    """Database transaction context manager with rollback support"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction: Optional[any] = None
    
    async def __aenter__(self) -> AsyncSession:
        self.transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.transaction.rollback()
        else:
            await self.transaction.commit()


# Convenience functions for app lifecycle
async def init_db() -> None:
    """Initialize database - called during app startup"""
    await db_manager.init_db()


async def close_db() -> None:
    """Close database connections - called during app shutdown"""
    await db_manager.close_db()


async def create_tables() -> None:
    """Create all tables - used in tests and initial setup"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created")


async def drop_tables() -> None:
    """Drop all tables - used in tests"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("✅ Database tables dropped")


# Database utilities
class DatabaseUtilities:
    """Database utility functions"""
    
    @staticmethod
    async def execute_raw_sql(sql: str, parameters: dict = None) -> any:
        """Execute raw SQL query"""
        async with get_db_context() as db:
            result = await db.execute(sql, parameters or {})
            return result
    
    @staticmethod
    async def get_table_count(table_name: str) -> int:
        """Get row count for a table"""
        sql = f"SELECT COUNT(*) FROM {table_name}"
        async with get_db_context() as db:
            result = await db.execute(sql)
            return result.scalar()
    
    @staticmethod
    async def truncate_table(table_name: str) -> None:
        """Truncate a table (for testing)"""
        sql = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"
        async with get_db_context() as db:
            await db.execute(sql)
            await db.commit()


# Export utilities
db_utils = DatabaseUtilities()

# Health check function for monitoring
async def database_health_check() -> dict:
    """Database health check for monitoring endpoints"""
    return await db_manager.health_check()