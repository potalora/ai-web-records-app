"""
Authentication service for handling user sessions and current user context.
"""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from ...database.client import db_client
from ..security.session import session_service
from ..security.encryption import encryption_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

# User model for dependency injection
class User(BaseModel):
    id: str
    email: str
    role: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    createdAt: str

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from the session token.
    """
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Validate session
        session_data = await session_service.validate_session(token)
        if not session_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session token"
            )
        
        # Get user from database
        user_record = await db_client.prisma.user.find_unique(
            where={"id": session_data["user"].id},
            include={"profile": True}
        )
        
        if not user_record:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        # Update last activity
        await db_client.prisma.usersession.update(
            where={"id": session_data["session_id"]},
            data={"lastActivity": datetime.utcnow()}
        )
        
        # Decrypt profile data if available
        firstName = None
        lastName = None
        if user_record.profile:
            try:
                if user_record.profile.firstName:
                    firstName = encryption_service.decrypt(
                        {"ciphertext": user_record.profile.firstName},
                        purpose="user_profile"
                    )
                if user_record.profile.lastName:
                    lastName = encryption_service.decrypt(
                        {"ciphertext": user_record.profile.lastName},
                        purpose="user_profile"
                    )
            except Exception as decrypt_error:
                logger.warning(f"Failed to decrypt profile data: {decrypt_error}")
                # Continue without names
                pass

        # Return user model
        return User(
            id=user_record.id,
            email=user_record.email,
            role=user_record.role,
            firstName=firstName,
            lastName=lastName,
            createdAt=user_record.createdAt.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal authentication error"
        )

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Optional dependency to get the current user if authenticated.
    Returns None if not authenticated.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None