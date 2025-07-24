#!/usr/bin/env python3
"""
Test if Prisma client can create users properly without raw SQL.
"""
import asyncio
import sys
import os
import time

# Add backend to path
sys.path.append('/Users/potalora/ai_workspace/ai_web_records_app/backend')

from src.database.client import db_client
from src.services.security.password import password_service
from prisma.enums import UserRole

async def test_prisma_user_creation():
    """Test user creation with Prisma client."""
    print("Testing Prisma user creation...")
    
    try:
        # Connect to database (it should be connected via the app)
        await db_client.connect()
        
        # Test user data
        test_email = f"prismatest{int(time.time())}@example.com"
        hashed_password = password_service.hash_password("TestPassword123!")
        
        print(f"Creating user with email: {test_email}")
        
        # Try creating user with Prisma client
        user = await db_client.prisma.user.create(
            data={
                "email": test_email,
                "password": hashed_password,
                "role": UserRole.PATIENT
            }
        )
        
        print(f"✓ User created successfully with Prisma client: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        
        # Clean up test user
        await db_client.prisma.user.delete(
            where={"id": user.id}
        )
        print("✓ Test user cleaned up")
        
        await db_client.disconnect()
        
    except Exception as e:
        print(f"✗ Prisma user creation failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prisma_user_creation())