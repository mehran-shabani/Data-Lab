"""Envelope Encryption service for securing sensitive data.

This module implements envelope encryption pattern:
1. Generate random Data Key for each secret
2. Encrypt data with Data Key using AES-GCM
3. Encrypt Data Key with Master Key from environment
4. Store encrypted data and encrypted Data Key

For MVP: Master Key loaded from SECRETS_MASTER_KEY env var.
For V1: Will be replaced with Vault/KMS integration.
"""

import base64
import json
import logging
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# Constants
DATA_KEY_SIZE = 32  # 256 bits
MASTER_KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12  # 96 bits (recommended for GCM)


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""

    pass


def load_master_key_from_env() -> bytes:
    """Load Master Key from environment variable.

    Master Key must be 32 bytes (256 bits).
    Can be provided as hex or base64 encoded string.

    Returns:
        bytes: The master key.

    Raises:
        EncryptionError: If master key is not configured or invalid.
    """
    master_key_str = os.getenv("SECRETS_MASTER_KEY")

    if not master_key_str:
        raise EncryptionError(
            "SECRETS_MASTER_KEY environment variable is not set. "
            "Application cannot start without a valid master key for envelope encryption."
        )

    # Try to decode as hex first, then base64
    try:
        # Try hex first
        if len(master_key_str) == 64:  # 32 bytes * 2 hex chars
            master_key = bytes.fromhex(master_key_str)
        else:
            # Try base64
            master_key = base64.b64decode(master_key_str)

        if len(master_key) != MASTER_KEY_SIZE:
            raise EncryptionError(
                f"Master key must be {MASTER_KEY_SIZE} bytes, got {len(master_key)} bytes"
            )

        return master_key

    except (ValueError, Exception) as e:
        raise EncryptionError(
            f"Failed to decode SECRETS_MASTER_KEY. "
            f"Provide as 64-char hex string or base64 encoded 32 bytes. Error: {e}"
        ) from e


def generate_data_key() -> bytes:
    """Generate a random Data Key for encrypting connection config.

    Returns:
        bytes: Random 32-byte data key.
    """
    return os.urandom(DATA_KEY_SIZE)


def encrypt_with_data_key(plaintext_data: dict[str, Any], data_key: bytes) -> bytes:
    """Encrypt data with Data Key using AES-GCM.

    Format: [nonce(12) || tag(16) || ciphertext]

    Args:
        plaintext_data: Dictionary to encrypt (will be JSON serialized).
        data_key: 32-byte encryption key.

    Returns:
        bytes: Encrypted data with nonce and tag prepended.

    Raises:
        EncryptionError: If encryption fails.
    """
    try:
        # Serialize to JSON
        plaintext_json = json.dumps(plaintext_data, sort_keys=True)
        plaintext_bytes = plaintext_json.encode("utf-8")

        # Generate nonce
        nonce = os.urandom(NONCE_SIZE)

        # Encrypt with AES-GCM
        aesgcm = AESGCM(data_key)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)

        # Combine: nonce || ciphertext_with_tag (tag is already appended by AESGCM)
        encrypted_blob = nonce + ciphertext_with_tag

        return encrypted_blob

    except Exception as e:
        logger.error("Encryption failed", exc_info=True)
        raise EncryptionError(f"Failed to encrypt data: {e}") from e


def decrypt_with_data_key(encrypted_blob: bytes, data_key: bytes) -> dict[str, Any]:
    """Decrypt data with Data Key using AES-GCM.

    Args:
        encrypted_blob: Encrypted data in format [nonce || tag || ciphertext].
        data_key: 32-byte encryption key.

    Returns:
        dict: Decrypted data.

    Raises:
        EncryptionError: If decryption fails.
    """
    try:
        # Extract nonce and ciphertext
        nonce = encrypted_blob[:NONCE_SIZE]
        ciphertext_with_tag = encrypted_blob[NONCE_SIZE:]

        # Decrypt with AES-GCM
        aesgcm = AESGCM(data_key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)

        # Deserialize JSON
        plaintext_json = plaintext_bytes.decode("utf-8")
        plaintext_data = json.loads(plaintext_json)

        return plaintext_data

    except Exception as e:
        logger.error("Decryption failed", exc_info=True)
        raise EncryptionError(f"Failed to decrypt data: {e}") from e


def wrap_key_with_master(data_key: bytes, master_key: bytes) -> bytes:
    """Wrap (encrypt) Data Key with Master Key using AES-GCM.

    Format: [nonce(12) || encrypted_key_with_tag]

    Args:
        data_key: The data key to wrap.
        master_key: The master key from environment.

    Returns:
        bytes: Wrapped data key.

    Raises:
        EncryptionError: If key wrapping fails.
    """
    try:
        # Generate nonce
        nonce = os.urandom(NONCE_SIZE)

        # Encrypt data key with master key
        aesgcm = AESGCM(master_key)
        encrypted_key_with_tag = aesgcm.encrypt(nonce, data_key, None)

        # Combine: nonce || encrypted_key_with_tag
        wrapped_key = nonce + encrypted_key_with_tag

        return wrapped_key

    except Exception as e:
        logger.error("Key wrapping failed", exc_info=True)
        raise EncryptionError(f"Failed to wrap key: {e}") from e


def unwrap_key_with_master(wrapped_key: bytes, master_key: bytes) -> bytes:
    """Unwrap (decrypt) Data Key with Master Key using AES-GCM.

    Args:
        wrapped_key: The wrapped data key from database.
        master_key: The master key from environment.

    Returns:
        bytes: Unwrapped data key.

    Raises:
        EncryptionError: If key unwrapping fails.
    """
    try:
        # Extract nonce and encrypted key
        nonce = wrapped_key[:NONCE_SIZE]
        encrypted_key_with_tag = wrapped_key[NONCE_SIZE:]

        # Decrypt data key with master key
        aesgcm = AESGCM(master_key)
        data_key = aesgcm.decrypt(nonce, encrypted_key_with_tag, None)

        return data_key

    except Exception as e:
        logger.error("Key unwrapping failed", exc_info=True)
        raise EncryptionError(f"Failed to unwrap key: {e}") from e


# Initialize and validate master key on module load
_master_key: bytes | None = None


def get_master_key() -> bytes:
    """Get the cached master key, loading it on first call.

    Returns:
        bytes: The master key.

    Raises:
        EncryptionError: If master key cannot be loaded.
    """
    global _master_key
    if _master_key is None:
        _master_key = load_master_key_from_env()
    return _master_key
