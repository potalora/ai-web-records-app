"""
Database client module for Prisma connection management.
Provides a singleton instance of the Prisma client with proper lifecycle management.
"""

import logging
from typing import Optional
from prisma import Prisma
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Singleton database client manager."""
    
    _instance: Optional['DatabaseClient'] = None
    _prisma: Optional[Prisma] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
        return cls._instance
    
    @property
    def prisma(self) -> Prisma:
        """Get or create Prisma client instance."""
        if self._prisma is None:
            self._prisma = Prisma()
        return self._prisma
    
    async def connect(self) -> None:
        """Connect to the database."""
        if not self._prisma:
            self._prisma = Prisma()
        
        if not self._prisma.is_connected():
            try:
                await self._prisma.connect()
                logger.info("Successfully connected to database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self._prisma and self._prisma.is_connected():
            await self._prisma.disconnect()
            logger.info("Disconnected from database")
    
    async def health_check(self) -> dict:
        """Check database health."""
        try:
            # Execute a simple query to check connection
            await self.prisma.query_raw('SELECT 1')
            return {
                "status": "healthy",
                "connected": self.prisma.is_connected()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connected": False
            }


# Global database client instance
db_client = DatabaseClient()


@asynccontextmanager
async def get_db():
    """
    Async context manager for database access.
    Ensures proper connection management.
    """
    try:
        await db_client.connect()
        yield db_client.prisma
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise
    # Connection remains open for reuse (singleton pattern)