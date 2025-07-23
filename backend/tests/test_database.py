"""
Test database connectivity and basic operations.
"""

import pytest
import asyncio
from datetime import datetime

from src.database import db_client
from src.services.security import (
    encryption_service,
    password_service,
    session_service,
    audit_service,
    AuditAction
)


@pytest.fixture
async def setup_database():
    """Setup database connection for tests."""
    await db_client.connect()
    yield
    await db_client.disconnect()


@pytest.mark.asyncio
async def test_database_connection(setup_database):
    """Test database connectivity."""
    health = await db_client.health_check()
    assert health["status"] == "healthy"
    assert health["connected"] is True


@pytest.mark.asyncio
async def test_encryption_service():
    """Test encryption and decryption."""
    # Test string encryption
    plaintext = "This is sensitive medical data"
    encrypted = encryption_service.encrypt(plaintext, purpose="test")
    
    assert encrypted["ciphertext"] != plaintext
    assert "iv" in encrypted
    assert "tag" in encrypted
    assert "salt" in encrypted
    
    # Test decryption
    decrypted = encryption_service.decrypt(encrypted, purpose="test")
    assert decrypted == plaintext
    
    # Test binary encryption
    binary_data = b"Binary medical data"
    encrypted_binary = encryption_service.encrypt_bytes(binary_data, purpose="test")
    decrypted_binary = encryption_service.decrypt_bytes(encrypted_binary, purpose="test")
    assert decrypted_binary == binary_data


def test_password_service():
    """Test password hashing and verification."""
    password = "SecurePassword123!"
    
    # Test password validation
    validation = password_service.validate_password_strength(password)
    assert validation["valid"] is True
    assert validation["strength"] in ["medium", "strong"]
    
    # Test hashing
    hashed = password_service.hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2b$")
    
    # Test verification
    assert password_service.verify_password(password, hashed) is True
    assert password_service.verify_password("wrong_password", hashed) is False
    
    # Test rehash detection
    assert password_service.needs_rehash(hashed) is False


@pytest.mark.asyncio
async def test_user_creation(setup_database):
    """Test creating a user with encrypted profile."""
    # Create a test user
    user_data = {
        "email": "test@example.com",
        "password": password_service.hash_password("TestPassword123!"),
        "role": "PATIENT",
        "termsAcceptedAt": datetime.utcnow(),
        "privacyAcceptedAt": datetime.utcnow()
    }
    
    user = await db_client.prisma.user.create(data=user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == "PATIENT"
    
    # Create encrypted profile
    profile_data = {
        "userId": user.id,
        "firstName": encryption_service.encrypt("John", purpose="user_data")["ciphertext"],
        "lastName": encryption_service.encrypt("Doe", purpose="user_data")["ciphertext"],
        "dateOfBirth": encryption_service.encrypt("1990-01-01", purpose="user_data")["ciphertext"]
    }
    
    profile = await db_client.prisma.userprofile.create(data=profile_data)
    
    assert profile.userId == user.id
    
    # Cleanup
    await db_client.prisma.userprofile.delete(where={"id": profile.id})
    await db_client.prisma.user.delete(where={"id": user.id})


@pytest.mark.asyncio
async def test_audit_logging(setup_database):
    """Test audit logging functionality."""
    # Create a test user for audit
    user = await db_client.prisma.user.create(
        data={
            "email": "audit_test@example.com",
            "password": "hashed_password"
        }
    )
    
    # Log an action
    await audit_service.log_action(
        user_id=user.id,
        action=AuditAction.CREATE,
        resource_type="TestResource",
        resource_id="test123",
        ip_address="127.0.0.1",
        user_agent="pytest",
        success=True
    )
    
    # Verify audit log was created
    audit_logs = await db_client.prisma.auditlog.find_many(
        where={"userId": user.id}
    )
    
    assert len(audit_logs) == 1
    assert audit_logs[0].action == "CREATE"
    assert audit_logs[0].resourceType == "TestResource"
    assert audit_logs[0].resourceId == "test123"
    assert audit_logs[0].success is True
    
    # Cleanup
    await db_client.prisma.auditlog.delete_many(where={"userId": user.id})
    await db_client.prisma.user.delete(where={"id": user.id})


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])