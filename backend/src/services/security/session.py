"""
Session management service for user authentication.
Handles session creation, validation, and cleanup.
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from ...database.client import db_client
from .password import password_service
from .audit import audit_service, AuditAction

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions."""
    
    def __init__(self):
        self.session_timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
        self.token_length = 32  # 256 bits
    
    def _generate_session_token(self) -> str:
        """Generate a secure random session token."""
        return secrets.token_urlsafe(self.token_length)
    
    def _hash_token(self, token: str) -> str:
        """Hash a session token for storage."""
        # We can use a simple hash here since tokens are random
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def create_session(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Dict[str, any]]:
        """
        Create a new session for a user.
        
        Args:
            email: User's email
            password: User's password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with session token and user info, or None if authentication fails
        """
        try:
            # Find user by email
            user = await db_client.prisma.user.find_unique(
                where={"email": email},
                include={"profile": True}
            )
            
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return None
            
            # Check if account is locked
            if user.accountLocked:
                logger.warning(f"Login attempt for locked account: {email}")
                try:
                    await audit_service.log_action(
                        user_id=user.id,
                        action=AuditAction.DENY_ACCESS.value,
                        resource_type="Session",
                        resource_id="LOGIN",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message="Account locked"
                    )
                except Exception as audit_error:
                    logger.warning(f"Audit logging failed for locked account access: {audit_error}")
                return None
            
            # Verify password
            if not password_service.verify_password(password, user.password):
                # Increment failed login count
                failed_count = user.failedLoginCount + 1
                
                # Lock account after 5 failed attempts
                if failed_count >= 5:
                    await db_client.prisma.user.update(
                        where={"id": user.id},
                        data={
                            "failedLoginCount": failed_count,
                            "accountLocked": True,
                            "accountLockedAt": datetime.utcnow()
                        }
                    )
                    logger.warning(f"Account locked due to failed login attempts: {email}")
                else:
                    await db_client.prisma.user.update(
                        where={"id": user.id},
                        data={"failedLoginCount": failed_count}
                    )
                
                try:
                    await audit_service.log_action(
                        user_id=user.id,
                        action=AuditAction.LOGIN.value,
                        resource_type="Session",
                        resource_id="LOGIN",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message="Invalid password"
                    )
                except Exception as audit_error:
                    logger.warning(f"Audit logging failed for invalid password attempt: {audit_error}")
                
                return None
            
            # Check if password needs rehashing
            if password_service.needs_rehash(user.password):
                new_hash = password_service.hash_password(password)
                await db_client.prisma.user.update(
                    where={"id": user.id},
                    data={"password": new_hash}
                )
            
            # Generate session token
            session_token = self._generate_session_token()
            hashed_token = self._hash_token(session_token)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(minutes=self.session_timeout_minutes)
            
            # Create session
            session = await db_client.prisma.usersession.create(
                data={
                    "userId": user.id,
                    "sessionToken": hashed_token,
                    "ipAddress": ip_address,
                    "userAgent": user_agent,
                    "expiresAt": expires_at
                }
            )
            
            # Update user login info
            await db_client.prisma.user.update(
                where={"id": user.id},
                data={
                    "lastLogin": datetime.utcnow(),
                    "failedLoginCount": 0  # Reset on successful login
                }
            )
            
            # Log successful login (temporarily disabled for debugging)
            try:
                await audit_service.log_action(
                    user_id=user.id,
                    action=AuditAction.LOGIN.value,
                    resource_type="Session",
                    resource_id=session.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
            except Exception as audit_error:
                logger.warning(f"Audit logging failed during login: {audit_error}")
                pass
            
            return {
                "token": session_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "profile": user.profile
                },
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return None
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Validate a session token and return user info.
        
        Args:
            session_token: The session token to validate
            ip_address: Optional IP address for verification
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            hashed_token = self._hash_token(session_token)
            
            # Find session
            session = await db_client.prisma.usersession.find_first(
                where={
                    "sessionToken": hashed_token,
                    "expiresAt": {"gt": datetime.utcnow()}
                },
                include={
                    "user": {
                        "include": {"profile": True}
                    }
                }
            )
            
            if not session:
                return None
            
            # Optionally verify IP address hasn't changed
            if ip_address and session.ipAddress != ip_address:
                logger.warning(
                    f"Session IP mismatch: expected {session.ipAddress}, got {ip_address}"
                )
                # Could implement stricter security by invalidating session
            
            # Update last activity
            await db_client.prisma.usersession.update(
                where={"id": session.id},
                data={"lastActivity": datetime.utcnow()}
            )
            
            return {
                "user": session.user,
                "session_id": session.id
            }
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None
    
    async def logout(
        self,
        session_token: str,
        user_id: str,
        ip_address: str
    ) -> bool:
        """
        Logout a user by invalidating their session.
        
        Args:
            session_token: The session token to invalidate
            user_id: User ID for audit logging
            ip_address: Client IP address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            hashed_token = self._hash_token(session_token)
            
            # Delete session
            result = await db_client.prisma.usersession.delete_many(
                where={"sessionToken": hashed_token}
            )
            
            # Log logout
            try:
                await audit_service.log_action(
                    user_id=user_id,
                    action=AuditAction.LOGOUT.value,
                    resource_type="Session",
                    resource_id="LOGOUT",
                    ip_address=ip_address,
                    success=True
                )
            except Exception as audit_error:
                logger.warning(f"Audit logging failed for logout: {audit_error}")
            
            return result.count > 0
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.
        This should be run periodically.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            result = await db_client.prisma.usersession.delete_many(
                where={"expiresAt": {"lt": datetime.utcnow()}}
            )
            
            if result.count > 0:
                logger.info(f"Cleaned up {result.count} expired sessions")
            
            return result.count
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            return 0
    
    async def invalidate_all_user_sessions(
        self,
        user_id: str,
        reason: str = "Security"
    ) -> int:
        """
        Invalidate all sessions for a user.
        Used for security events or password changes.
        
        Args:
            user_id: User whose sessions to invalidate
            reason: Reason for invalidation
            
        Returns:
            Number of sessions invalidated
        """
        try:
            result = await db_client.prisma.usersession.delete_many(
                where={"userId": user_id}
            )
            
            if result.count > 0:
                logger.info(
                    f"Invalidated {result.count} sessions for user {user_id}: {reason}"
                )
                
                try:
                    await audit_service.log_action(
                        user_id=user_id,
                        action=AuditAction.LOGOUT.value,
                        resource_type="Session",
                        resource_id="ALL_SESSIONS",
                        ip_address="system",
                        success=True,
                        error_message=f"All sessions invalidated: {reason}"
                    )
                except Exception as audit_error:
                    logger.warning(f"Audit logging failed for session invalidation: {audit_error}")
            
            return result.count
            
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            return 0


# Global session service instance
session_service = SessionService()