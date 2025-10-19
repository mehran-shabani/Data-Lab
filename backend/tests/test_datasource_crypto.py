"""Tests for envelope encryption functionality."""

import os

import pytest

from apps.core.crypto import (
    EncryptionError,
    decrypt_with_data_key,
    encrypt_with_data_key,
    generate_data_key,
    get_master_key,
    load_master_key_from_env,
    unwrap_key_with_master,
    wrap_key_with_master,
)


@pytest.fixture(autouse=True)
def set_master_key_env(monkeypatch):
    """Set SECRETS_MASTER_KEY for tests."""
    # 32 bytes as hex string
    test_master_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    monkeypatch.setenv("SECRETS_MASTER_KEY", test_master_key)
    # Clear cached master key
    import apps.core.crypto

    apps.core.crypto._master_key = None


def test_generate_data_key():
    """Test data key generation."""
    key1 = generate_data_key()
    key2 = generate_data_key()

    # Should be 32 bytes
    assert len(key1) == 32
    assert len(key2) == 32

    # Should be random (different each time)
    assert key1 != key2


def test_encrypt_decrypt_with_data_key():
    """Test encryption and decryption with data key."""
    data_key = generate_data_key()
    plaintext = {"username": "test_user", "password": "secret123", "host": "localhost"}

    # Encrypt
    encrypted_blob = encrypt_with_data_key(plaintext, data_key)
    assert isinstance(encrypted_blob, bytes)
    assert len(encrypted_blob) > 0

    # Decrypt
    decrypted = decrypt_with_data_key(encrypted_blob, data_key)
    assert decrypted == plaintext


def test_encrypt_with_different_keys_produces_different_ciphertext():
    """Test that same plaintext with different keys produces different ciphertext."""
    plaintext = {"secret": "data"}
    key1 = generate_data_key()
    key2 = generate_data_key()

    encrypted1 = encrypt_with_data_key(plaintext, key1)
    encrypted2 = encrypt_with_data_key(plaintext, key2)

    assert encrypted1 != encrypted2


def test_decrypt_with_wrong_key_fails():
    """Test that decryption with wrong key fails."""
    data_key = generate_data_key()
    wrong_key = generate_data_key()
    plaintext = {"secret": "data"}

    encrypted = encrypt_with_data_key(plaintext, data_key)

    # Should raise EncryptionError
    with pytest.raises(EncryptionError):
        decrypt_with_data_key(encrypted, wrong_key)


def test_wrap_unwrap_key_with_master():
    """Test key wrapping and unwrapping with master key."""
    master_key = get_master_key()
    data_key = generate_data_key()

    # Wrap
    wrapped_key = wrap_key_with_master(data_key, master_key)
    assert isinstance(wrapped_key, bytes)
    assert len(wrapped_key) > 0

    # Unwrap
    unwrapped_key = unwrap_key_with_master(wrapped_key, master_key)
    assert unwrapped_key == data_key


def test_unwrap_with_wrong_master_key_fails():
    """Test that unwrapping with wrong master key fails."""
    master_key = get_master_key()
    wrong_master_key = os.urandom(32)
    data_key = generate_data_key()

    wrapped_key = wrap_key_with_master(data_key, master_key)

    # Should raise EncryptionError
    with pytest.raises(EncryptionError):
        unwrap_key_with_master(wrapped_key, wrong_master_key)


def test_load_master_key_from_env():
    """Test loading master key from environment."""
    master_key = load_master_key_from_env()
    assert isinstance(master_key, bytes)
    assert len(master_key) == 32


def test_load_master_key_missing_env_var(monkeypatch):
    """Test that missing SECRETS_MASTER_KEY raises error."""
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    import apps.core.crypto

    apps.core.crypto._master_key = None

    with pytest.raises(EncryptionError, match="SECRETS_MASTER_KEY environment variable is not set"):
        load_master_key_from_env()


def test_load_master_key_invalid_hex(monkeypatch):
    """Test that invalid hex raises error."""
    monkeypatch.setenv("SECRETS_MASTER_KEY", "not-a-valid-hex")
    import apps.core.crypto

    apps.core.crypto._master_key = None

    with pytest.raises(EncryptionError, match="Failed to decode"):
        load_master_key_from_env()


def test_full_envelope_encryption_flow():
    """Test complete envelope encryption flow."""
    # Simulate creating a datasource
    connection_config = {
        "host": "db.example.com",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "supersecret",
    }

    # 1. Generate data key
    data_key = generate_data_key()

    # 2. Encrypt config with data key
    config_encrypted = encrypt_with_data_key(connection_config, data_key)

    # 3. Wrap data key with master key
    master_key = get_master_key()
    data_key_encrypted = wrap_key_with_master(data_key, master_key)

    # Simulate storing in DB: config_encrypted and data_key_encrypted

    # Simulate loading from DB
    # 4. Unwrap data key with master key
    data_key_unwrapped = unwrap_key_with_master(data_key_encrypted, master_key)

    # 5. Decrypt config with data key
    config_decrypted = decrypt_with_data_key(config_encrypted, data_key_unwrapped)

    # Verify original data
    assert config_decrypted == connection_config
