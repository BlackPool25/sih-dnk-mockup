"""Tests for auth.services.password — bcrypt hashing and verification."""

from auth.services.password import hash_password, verify_password


def test_hash_and_verify():
    """Hashing a password and verifying it with the same plain text returns True."""
    hashed = hash_password("s3cret!")
    assert verify_password("s3cret!", hashed) is True


def test_wrong_password():
    """Verifying with an incorrect plain password returns False."""
    hashed = hash_password("s3cret!")
    assert verify_password("wrong-password", hashed) is False


def test_different_salts():
    """Hashing the same password twice produces different hash strings (salts differ)."""
    h1 = hash_password("s3cret!")
    h2 = hash_password("s3cret!")
    assert h1 != h2
    # Both should still verify correctly
    assert verify_password("s3cret!", h1) is True
    assert verify_password("s3cret!", h2) is True


def test_hash_output_is_string():
    """hash_password returns a string, not bytes."""
    result = hash_password("password123")
    assert isinstance(result, str)
    assert result.startswith("$2")  # bcrypt identifiers


def test_empty_password():
    """Hash and verify an empty password string."""
    hashed = hash_password("")
    assert verify_password("", hashed) is True
    assert verify_password("something", hashed) is False
