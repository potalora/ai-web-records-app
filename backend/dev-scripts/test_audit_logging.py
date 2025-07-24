#!/usr/bin/env python3
"""
Test audit logging in isolation to identify the root cause of failures.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append('/Users/potalora/ai_workspace/ai_web_records_app/backend')

from src.services.security.audit import audit_service, AuditAction
from src.database.client import db_client

async def test_audit_logging():
    """Test audit logging functionality."""
    print("Testing audit logging...")
    
    try:
        # Test with enum value
        print("\n1. Testing with AuditAction.CREATE enum...")
        await audit_service.log_action(
            user_id="test-user-123",
            action=AuditAction.CREATE,
            resource_type="User",
            resource_id="test-resource-123",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=True
        )
        print("✓ Enum test passed")
        
        # Test with string value
        print("\n2. Testing with string action...")
        await audit_service.log_action(
            user_id="test-user-124",
            action="CREATE",
            resource_type="User", 
            resource_id="test-resource-124",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            success=True
        )
        print("✓ String test passed")
        
        # Check if records were created
        print("\n3. Checking database for audit records...")
        records = await db_client.prisma.auditlog.find_many(
            where={"userId": {"in": ["test-user-123", "test-user-124"]}},
            take=5
        )
        print(f"✓ Found {len(records)} audit records in database")
        
        # Clean up test records
        await db_client.prisma.auditlog.delete_many(
            where={"userId": {"in": ["test-user-123", "test-user-124"]}}
        )
        print("✓ Cleaned up test records")
        
    except Exception as e:
        print(f"✗ Audit logging test failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audit_logging())