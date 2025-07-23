"""
Authentication routes for user registration, login, and session management.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from ..database import db_client
from ..services.security import (
    password_service,
    session_service,
    audit_service,
    encryption_service,
    AuditAction
)

router = APIRouter(prefix="/auth", tags=["authentication"])


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
        user = await db_client.prisma.user.create({
            "data": {
                "email": request.email,
                "password": hashed_password,
                "role": "PATIENT",
                "termsAcceptedAt": datetime.utcnow() if request.acceptTerms else None,
                "privacyAcceptedAt": datetime.utcnow() if request.acceptPrivacy else None
            }
        })
        
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
        
        # Create user profile with encrypted data
        profile = await db_client.prisma.userprofile.create({
            "data": {
                "userId": user.id,
                "firstName": encrypted_first_name["ciphertext"],
                "lastName": encrypted_last_name["ciphertext"],
                "dateOfBirth": encrypted_dob["ciphertext"],
                "phone": encrypted_phone["ciphertext"] if encrypted_phone else None
            }
        })
        
        # Log registration
        await audit_service.log_action(
            user_id=user.id,
            action=AuditAction.CREATE,
            resource_type="User",
            resource_id=user.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            success=True
        )
        
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
        # Log failed registration attempt
        await audit_service.log_action(
            user_id=None,
            action=AuditAction.CREATE,
            resource_type="User",
            resource_id="registration_attempt",
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            success=False,
            error_message=str(e)
        )
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
async def validate_session(req: Request, token: str = Depends(lambda: None)):
    """
    Validate a session token.
    Note: In production, get token from Authorization header.
    """
    if not token:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    session_data = await session_service.validate_session(
        token,
        ip_address=req.client.host if req.client else None
    )
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "valid": True,
        "user": {
            "id": session_data["user"].id,
            "email": session_data["user"].email,
            "role": session_data["user"].role
        }
    }


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
            action=AuditAction.UPDATE,
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
        action=AuditAction.UPDATE,
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