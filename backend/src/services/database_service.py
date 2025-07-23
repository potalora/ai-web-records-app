"""
Database Service

Simple wrapper for accessing the database client.
"""

from ..database.client import db_client

def get_database():
    """Get the database client instance"""
    return db_client.prisma