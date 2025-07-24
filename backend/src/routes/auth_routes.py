"""
Authentication routes for user registration, login, and session management.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import logging

from ..database import db_client
from ..services.security import (
    password_service,
    session_service,
    audit_service,
    encryption_service,
    AuditAction
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# HTTP Bearer security for session validation
security = HTTPBearer()

# Logger
logger = logging.getLogger(__name__)


# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    dateOfBirth: str  # Format: YYYY-MM-DD
    phone: Optional[str] = None
    acceptTerms: bool
    acceptPrivacy: bool
    
    @field_validator('password')
    def validate_password(cls, v):
        result = password_service.validate_password_strength(v)
        if not result["valid"]:
            raise ValueError("; ".join(result["errors"]))
        return v
    
    @field_validator('acceptTerms', 'acceptPrivacy')
    def validate_acceptance(cls, v, info):
        if not v:
            raise ValueError(f"Must accept {info.field_name}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionResponse(BaseModel):
    token: str
    user: dict
    expiresAt: datetime


class MessageResponse(BaseModel):
    message: str


def get_client_info(request: Request) -> dict:
    """Extract client information from request."""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }


@router.post("/register", response_model=SessionResponse)
async def register(request: RegisterRequest, req: Request):
    """
    Register a new user with encrypted personal information.
    """
    client_info = get_client_info(req)
    
    try:
        # Check if user already exists
        existing_user = await db_client.prisma.user.find_unique(
            where={"email": request.email}
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = password_service.hash_password(request.password)
        
        # Create user
        logger.info(f"Creating user with email: {request.email}")
        # Import the UserRole enum from Prisma
        from prisma.enums import UserRole
        
        # Try with minimal required fields only
        user_data = {
            "email": request.email,
            "password": hashed_password,
            "role": UserRole.PATIENT
        }
        logger.info(f"User data: {user_data}")
        
        try:
            # TEMPORARY WORKAROUND: Use raw SQL due to Prisma client issue
            logger.info("Using raw SQL workaround for user creation")
            import uuid
            user_id = str(uuid.uuid4()).replace('-', '')[:25]  # Generate CUID-like ID
            
            result = await db_client.prisma.execute_raw(
                """
                INSERT INTO "User" (id, email, password, role, "createdAt", "updatedAt")
                VALUES ($1, $2, $3, 'PATIENT'::"UserRole", NOW(), NOW())
                RETURNING id, email, role, "createdAt", "updatedAt"
                """,
                user_id,
                request.email,
                hashed_password
            )
            
            # Create a user-like object for the rest of the code
            class MockUser:
                def __init__(self, user_id, email, role):
                    self.id = user_id
                    self.email = email
                    self.role = role
            
            user = MockUser(user_id, request.email, "PATIENT")
            logger.info(f"User created successfully via raw SQL: {user.id}")
            
        except Exception as db_error:
            logger.error(f"Database error during user creation: {db_error}")
            logger.error(f"Error type: {type(db_error)}")
            raise
        
        # Encrypt personal information
        encrypted_first_name = encryption_service.encrypt(
            request.firstName, purpose="user_profile"
        )
        encrypted_last_name = encryption_service.encrypt(
            request.lastName, purpose="user_profile"
        )
        encrypted_dob = encryption_service.encrypt(
            request.dateOfBirth, purpose="user_profile"
        )
        
        encrypted_phone = None
        if request.phone:
            encrypted_phone = encryption_service.encrypt(
                request.phone, purpose="user_profile"
            )
        
        # Create user profile with encrypted data using raw SQL workaround
        try:
            logger.info("Creating user profile via raw SQL")
            profile_id = str(uuid.uuid4()).replace('-', '')[:25]  # Generate CUID-like ID
            
            await db_client.prisma.execute_raw(
                """
                INSERT INTO "UserProfile" (id, "userId", "firstName", "lastName", "dateOfBirth", phone, "createdAt", "updatedAt")
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                """,
                profile_id,
                user.id,
                encrypted_first_name["ciphertext"],
                encrypted_last_name["ciphertext"],
                encrypted_dob["ciphertext"],
                encrypted_phone["ciphertext"] if encrypted_phone else None
            )
            logger.info(f"User profile created successfully via raw SQL: {profile_id}")
            
        except Exception as profile_error:
            logger.error(f"Failed to create user profile: {profile_error}")
            # Continue without profile for now - user can complete it later
            pass
        
        # Log registration (temporarily disabled for debugging)
        try:
            await audit_service.log_action(
                user_id=user.id,
                action=AuditAction.CREATE.value,
                resource_type="User",
                resource_id=user.id,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                success=True
            )
        except Exception as audit_error:
            # Don't fail registration due to audit logging issues
            logger.warning(f"Audit logging failed during registration: {audit_error}")
            pass
        
        # Create session
        session_data = await session_service.create_session(
            email=request.email,
            password=request.password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return SessionResponse(
            token=session_data["token"],
            user={
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "firstName": request.firstName,  # Return unencrypted for display
                "lastName": request.lastName
            },
            expiresAt=session_data["expires_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed registration attempt (temporarily disabled for debugging)
        try:
            await audit_service.log_action(
                user_id=None,
                action=AuditAction.CREATE.value,
                resource_type="User",
                resource_id="registration_attempt",
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                success=False,
                error_message=str(e)
            )
        except Exception as audit_error:
            logger.warning(f"Audit logging failed during registration error: {audit_error}")
            pass
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=SessionResponse)
async def login(request: LoginRequest, req: Request):
    """
    Login with email and password.
    """
    client_info = get_client_info(req)
    
    # Create session
    session_data = await session_service.create_session(
        email=request.email,
        password=request.password,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )
    
    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Decrypt user profile data for response
    user_data = session_data["user"]
    if user_data.get("profile"):
        profile = user_data["profile"]
        try:
            # Decrypt first and last name for display
            if profile.get("firstName"):
                decrypted_first = encryption_service.decrypt(
                    {"ciphertext": profile["firstName"]},
                    purpose="user_profile"
                )
                user_data["firstName"] = decrypted_first
                
            if profile.get("lastName"):
                decrypted_last = encryption_service.decrypt(
                    {"ciphertext": profile["lastName"]},
                    purpose="user_profile"
                )
                user_data["lastName"] = decrypted_last
        except:
            # If decryption fails, don't include names
            pass
        
        # Remove encrypted profile from response
        del user_data["profile"]
    
    return SessionResponse(
        token=session_data["token"],
        user=user_data,
        expiresAt=session_data["expires_at"]
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(req: Request, token: str = Depends(lambda: None)):
    """
    Logout and invalidate session.
    Note: In production, get token from Authorization header.
    """
    client_info = get_client_info(req)
    
    # For now, we'll expect the token in the request body
    # In production, this should come from Authorization header
    if not token:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    # Validate session to get user ID
    session_data = await session_service.validate_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Logout
    success = await session_service.logout(
        session_token=token,
        user_id=session_data["user"].id,
        ip_address=client_info["ip_address"]
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed")
    
    return MessageResponse(message="Logged out successfully")


@router.get("/session/validate")
async def validate_session(
    req: Request, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validate a session token using Authorization header.
    """
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Validate session
        session_data = await session_service.validate_session(
            token,
            ip_address=req.client.host if req.client else None
        )
        
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
        
        return {
            "valid": True,
            "user": {
                "id": user_record.id,
                "email": user_record.email,
                "role": user_record.role,
                "firstName": firstName,
                "lastName": lastName
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        logger.error(f"Error type: {type(e)}")
        raise HTTPException(
            status_code=500,
            detail="Session validation failed"
        )


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    old_password: str,
    new_password: str,
    req: Request,
    token: str = Depends(lambda: None)
):
    """
    Change user password.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate session
    session_data = await session_service.validate_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = session_data["user"]
    client_info = get_client_info(req)
    
    # Verify old password
    if not password_service.verify_password(old_password, user.password):
        await audit_service.log_action(
            user_id=user.id,
            action=AuditAction.UPDATE.value,
            resource_type="User",
            resource_id=user.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            success=False,
            error_message="Invalid old password"
        )
        raise HTTPException(status_code=401, detail="Invalid old password")
    
    # Validate new password
    validation = password_service.validate_password_strength(new_password)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail="; ".join(validation["errors"])
        )
    
    # Update password
    new_hash = password_service.hash_password(new_password)
    await db_client.prisma.user.update(
        where={"id": user.id},
        data={"password": new_hash}
    )
    
    # Log password change
    await audit_service.log_action(
        user_id=user.id,
        action=AuditAction.UPDATE.value,
        resource_type="User",
        resource_id=user.id,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        success=True,
        new_values={"field": "password"}
    )
    
    # Invalidate all sessions for security
    await session_service.invalidate_all_user_sessions(
        user.id,
        reason="Password changed"
    )
    
    return MessageResponse(message="Password changed successfully. Please login again.")