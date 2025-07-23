"""
Database module.
Provides database client and related utilities.
"""

from .client import db_client, get_db

__all__ = ['db_client', 'get_db']