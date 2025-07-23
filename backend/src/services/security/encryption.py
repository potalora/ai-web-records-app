"""
Encryption service for securing sensitive data.
Implements AES-256-GCM encryption with proper key management.
"""

import os
import base64
import logging
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        self.algorithm = "AES-256-GCM"
        self._master_key = self._load_or_create_master_key()
    
    def _load_or_create_master_key(self) -> bytes:
        """Load or create the master encryption key."""
        key_file = os.getenv("MASTER_KEY_FILE", "./keys/master.key")
        
        # Create keys directory if it doesn't exist
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        try:
            # Try to load existing key
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    key = f.read()
                    if len(key) == 32:  # 256 bits
                        logger.info("Loaded existing master key")
                        return key
                    else:
                        logger.warning("Invalid master key size, generating new one")
            
            # Generate new key
            key = os.urandom(32)  # 256 bits
            with open(key_file, "wb") as f:
                f.write(key)
            
            # Set restrictive permissions (owner read only)
            os.chmod(key_file, 0o400)
            
            logger.info("Generated new master key")
            return key
            
        except Exception as e:
            logger.error(f"Failed to load/create master key: {e}")
            raise
    
    def derive_key(self, purpose: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive a purpose-specific key from the master key.
        
        Args:
            purpose: The purpose of the key (e.g., "user_data", "health_records")
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(self._master_key + purpose.encode())
        return key, salt
    
    def encrypt(self, plaintext: str, purpose: str = "general") -> dict:
        """
        Encrypt a string using AES-256-GCM.
        
        Args:
            plaintext: The string to encrypt
            purpose: The purpose of encryption (for key derivation)
            
        Returns:
            Dictionary containing encrypted data, IV, auth tag, and salt
        """
        try:
            # Generate IV and derive key
            iv = os.urandom(12)  # 96 bits for GCM
            key, salt = self.derive_key(purpose)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt
            ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
            
            return {
                "ciphertext": base64.b64encode(ciphertext).decode(),
                "iv": base64.b64encode(iv).decode(),
                "tag": base64.b64encode(encryptor.tag).decode(),
                "salt": base64.b64encode(salt).decode(),
                "algorithm": self.algorithm
            }
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: dict, purpose: str = "general") -> str:
        """
        Decrypt data encrypted with encrypt().
        
        Args:
            encrypted_data: Dictionary containing ciphertext, iv, tag, salt
            purpose: The purpose used during encryption
            
        Returns:
            Decrypted string
        """
        try:
            # Decode from base64
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            iv = base64.b64decode(encrypted_data["iv"])
            tag = base64.b64decode(encrypted_data["tag"])
            salt = base64.b64decode(encrypted_data["salt"])
            
            # Derive key with same salt
            key, _ = self.derive_key(purpose, salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_bytes(self, data: bytes, purpose: str = "general") -> dict:
        """
        Encrypt binary data using AES-256-GCM.
        
        Args:
            data: The bytes to encrypt
            purpose: The purpose of encryption
            
        Returns:
            Dictionary containing encrypted data, IV, auth tag, and salt
        """
        try:
            # Generate IV and derive key
            iv = os.urandom(12)
            key, salt = self.derive_key(purpose)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            return {
                "ciphertext": ciphertext,  # Return as bytes
                "iv": base64.b64encode(iv).decode(),
                "tag": base64.b64encode(encryptor.tag).decode(),
                "salt": base64.b64encode(salt).decode(),
                "algorithm": self.algorithm
            }
            
        except Exception as e:
            logger.error(f"Binary encryption failed: {e}")
            raise
    
    def decrypt_bytes(self, encrypted_data: dict, purpose: str = "general") -> bytes:
        """
        Decrypt binary data encrypted with encrypt_bytes().
        
        Args:
            encrypted_data: Dictionary containing ciphertext (bytes), iv, tag, salt
            purpose: The purpose used during encryption
            
        Returns:
            Decrypted bytes
        """
        try:
            # Get ciphertext (already bytes)
            ciphertext = encrypted_data["ciphertext"]
            
            # Decode other fields from base64
            iv = base64.b64decode(encrypted_data["iv"])
            tag = base64.b64decode(encrypted_data["tag"])
            salt = base64.b64decode(encrypted_data["salt"])
            
            # Derive key with same salt
            key, _ = self.derive_key(purpose, salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Binary decryption failed: {e}")
            raise


# Global encryption service instance
encryption_service = EncryptionService()