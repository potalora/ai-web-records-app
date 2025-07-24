#!/usr/bin/env python3
"""
Check if audit logs are being created in the database.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append('/Users/potalora/ai_workspace/ai_web_records_app/backend')

from src.database.client import db_client

async def check_audit_logs():
    """Check recent audit logs in database."""
    print("Checking audit logs in database...")
    
    try:
        # Connect to database
        await db_client.connect()
        
        # Get recent audit logs
        logs = await db_client.prisma.auditlog.find_many(
            order={"timestamp": "desc"},
            take=10
        )
        
        print(f"Found {len(logs)} recent audit log entries:")
        for log in logs:
            print(f"- {log.timestamp}: User {log.userId} performed {log.action} on {log.resourceType}/{log.resourceId}")
        
        # Disconnect
        await db_client.disconnect()
        
    except Exception as e:
        print(f"Error checking audit logs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_audit_logs())