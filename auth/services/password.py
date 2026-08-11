"""Password hashing and verification using bcrypt via passlib.

Uses ``passlib.context.CryptContext`` with the ``bcrypt`` scheme so that
callers get a hash string that is safe to store and can be verified later
without knowing the original password.
"""

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        A bcrypt hash string (includes the salt).
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The password to check.
        hashed_password: The stored bcrypt hash.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)
