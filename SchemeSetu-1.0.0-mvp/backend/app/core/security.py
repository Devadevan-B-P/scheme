"""
Security utilities: password hashing and verification using PBKDF2-SHA256.
"""

import hashlib
import os


def hash_password(password: str) -> str:
    """Hash password using SHA256 PBKDF2 with 100,000 iterations and salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against salt and key hash."""
    try:
        salt_hex, key_hex = password_hash.split('$')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False
