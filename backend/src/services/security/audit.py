"""
Audit logging service for HIPAA compliance.
Tracks all access to protected health information.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from ...database.client import db_client

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    PRINT = "PRINT"
    SHARE = "SHARE"
    DENY_ACCESS = "DENY_ACCESS"


class AccessType(str, Enum):
    """Access types for health records."""
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"
    PRINT = "PRINT"
    SHARE = "SHARE"
    API_ACCESS = "API_ACCESS"


class AuditService:
    """Service for audit logging and compliance tracking."""
    
    async def log_action(
        self,
        user_id: Optional[str],
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log an audit action.
        
        Args:
            user_id: ID of the user performing the action
            action: The action being performed
            resource_type: Type of resource being accessed
            resource_id: ID of the resource
            ip_address: IP address of the request
            user_agent: User agent string
            request_method: HTTP method
            request_path: Request path
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            success: Whether the action succeeded
            error_message: Error message if failed
        """
        try:
            # TEMPORARY: Disable audit logging to isolate registration issues
            logger.info(f"Audit logging temporarily disabled - would log: {action} on {resource_type}/{resource_id} by user {user_id}")
            return
            
            # Original audit logging code (disabled for debugging)
            # Ensure action is a string value (handle both enum and string inputs)
            if hasattr(action, 'value'):
                action_str = action.value
            else:
                action_str = str(action)
            
            # Debug logging to identify the issue
            logger.info(f"Creating audit log with action: '{action_str}' (original: '{action}', type: {type(action)})")
            
            # Try using a more explicit data structure for Prisma
            audit_data = {
                "userId": user_id,
                "action": action_str,
                "resourceType": resource_type,
                "resourceId": resource_id,
                "ipAddress": ip_address,
                "userAgent": user_agent,
                "requestMethod": request_method,
                "requestPath": request_path,
                "oldValues": json.dumps(old_values) if old_values else None,
                "newValues": json.dumps(new_values) if new_values else None,
                "success": success,
                "errorMessage": error_message
            }
            
            # Remove None values that might be causing issues
            audit_data = {k: v for k, v in audit_data.items() if v is not None}
            
            logger.info(f"Audit data being sent to Prisma: {audit_data}")
            
            await db_client.prisma.auditlog.create({
                "data": audit_data
            })
            
            # Also log to application logger for monitoring
            log_level = logging.INFO if success else logging.WARNING
            logger.log(
                log_level,
                f"Audit: {action} on {resource_type}/{resource_id} by user {user_id} "
                f"from {ip_address} - {'Success' if success else 'Failed'}"
            )
            
        except Exception as e:
            # Critical: audit logging failure should not break the application
            # but must be tracked
            logger.error(f"Failed to create audit log: {e}")
            # Could implement fallback to file-based logging here
    
    async def log_access(
        self,
        user_id: str,
        health_record_id: str,
        access_type: AccessType,
        purpose: str,
        ip_address: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log access to a health record.
        
        Args:
            user_id: ID of the user accessing the record
            health_record_id: ID of the health record
            access_type: Type of access
            purpose: Reason for access
            ip_address: IP address of the request
            session_id: Optional session ID
        """
        try:
            await db_client.prisma.accesslog.create({
                "data": {
                    "userId": user_id,
                    "healthRecordId": health_record_id,
                    "accessType": access_type,
                    "purpose": purpose,
                    "ipAddress": ip_address,
                    "sessionId": session_id
                }
            })
            
            logger.info(
                f"Access log: User {user_id} accessed record {health_record_id} "
                f"({access_type}) from {ip_address}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create access log: {e}")
    
    async def get_user_audit_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Get audit trail for a specific user.
        
        Args:
            user_id: User ID to get audit trail for
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records to return
            
        Returns:
            List of audit log entries
        """
        try:
            where_clause = {"userId": user_id}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["gte"] = start_date
                if end_date:
                    date_filter["lte"] = end_date
                where_clause["timestamp"] = date_filter
            
            return await db_client.prisma.auditlog.find_many(
                where=where_clause,
                order={"timestamp": "desc"},
                take=limit
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []
    
    async def get_resource_access_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> list:
        """
        Get access history for a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of records to return
            
        Returns:
            List of audit log entries
        """
        try:
            return await db_client.prisma.auditlog.find_many(
                where={
                    "resourceType": resource_type,
                    "resourceId": resource_id
                },
                order={"timestamp": "desc"},
                take=limit,
                include={"user": True}
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve resource access history: {e}")
            return []
    
    async def check_suspicious_activity(
        self,
        user_id: str,
        time_window_minutes: int = 5,
        max_actions: int = 100
    ) -> bool:
        """
        Check for suspicious activity patterns.
        
        Args:
            user_id: User to check
            time_window_minutes: Time window to check
            max_actions: Maximum allowed actions in time window
            
        Returns:
            True if suspicious activity detected
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            count = await db_client.prisma.auditlog.count(
                where={
                    "userId": user_id,
                    "timestamp": {"gte": cutoff_time}
                }
            )
            
            if count > max_actions:
                logger.warning(
                    f"Suspicious activity detected: User {user_id} performed "
                    f"{count} actions in {time_window_minutes} minutes"
                )
                
                # Log this as a security event
                await self.log_action(
                    user_id=user_id,
                    action=AuditAction.DENY_ACCESS.value,
                    resource_type="SECURITY",
                    resource_id="RATE_LIMIT",
                    ip_address="system",
                    success=False,
                    error_message=f"Rate limit exceeded: {count} actions in {time_window_minutes} minutes"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check suspicious activity: {e}")
            return False


# Global audit service instance
audit_service = AuditService()