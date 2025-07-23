#!/usr/bin/env python3
"""
Script to generate master encryption key for the application.
Run this once during initial setup.
"""

import os
import secrets
from pathlib import Path

def generate_master_key():
    """Generate and save master encryption key."""
    
    # Create keys directory
    keys_dir = Path("./keys")
    keys_dir.mkdir(exist_ok=True)
    
    key_file = keys_dir / "master.key"
    
    # Check if key already exists
    if key_file.exists():
        print(f"Master key already exists at {key_file}")
        response = input("Do you want to regenerate it? This will make existing encrypted data unreadable! (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing key.")
            return
    
    # Generate 256-bit key
    master_key = secrets.token_bytes(32)
    
    # Write to file with restrictive permissions
    with open(key_file, "wb") as f:
        f.write(master_key)
    
    # Set file permissions (owner read only)
    os.chmod(key_file, 0o400)
    
    print(f"Master key generated and saved to {key_file}")
    print(f"Key length: {len(master_key)} bytes (256 bits)")
    print("IMPORTANT: Keep this key secure and backed up!")
    print("WARNING: If you lose this key, all encrypted data will be unrecoverable!")

def generate_session_secret():
    """Generate a random session secret."""
    
    secret = secrets.token_urlsafe(64)
    
    print("\nSession secret generated:")
    print(f"SESSION_SECRET={secret}")
    print("\nAdd this to your .env file or use as an environment variable.")

if __name__ == "__main__":
    print("=== AI Health Records - Key Setup ===")
    print()
    
    generate_master_key()
    generate_session_secret()
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Update your .env file with the session secret above")
    print("2. Ensure PostgreSQL is running")
    print("3. Run the database setup script: ./scripts/setup_database.sh")
    print("4. Push the schema: prisma db push")
    print("5. Start the application: uvicorn main:app --reload")