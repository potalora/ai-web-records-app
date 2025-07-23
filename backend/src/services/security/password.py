"""
Password hashing and verification service.
Uses bcrypt for secure password storage.
"""

import os
import bcrypt
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PasswordService:
    """Service for password hashing and verification."""
    
    def __init__(self):
        self.rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plaintext password to hash
            
        Returns:
            The hashed password string
        """
        try:
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: The plaintext password to verify
            hashed: The hashed password to check against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if a password hash needs to be rehashed.
        This happens when the cost factor has been increased.
        
        Args:
            hashed: The hashed password to check
            
        Returns:
            True if rehashing is needed, False otherwise
        """
        try:
            # Extract the cost factor from the hash
            # bcrypt format: $2b$<cost>$<salt><hash>
            parts = hashed.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
            return True
        except:
            return True
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Validate password strength according to security requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check length (minimum 8 characters)
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Check for uppercase letter
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        # Check for special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        # Calculate strength score
        score = 0
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in special_chars for c in password):
            score += 1
        
        strength = "weak"
        if score >= 5:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": score
        }


# Global password service instance
password_service = PasswordService()