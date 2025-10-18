"""Security utilities for authentication and JWT tokens."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(claims: dict, ttl_min: int | None = None) -> str:
    """
    Create JWT access token with HS256 algorithm.

    Args:
        claims: Dictionary of claims to include in the token.
                Expected keys: sub, email, org_id, roles
        ttl_min: Time to live in minutes. If None, uses AUTH_ACCESS_TTL_MIN from settings.

    Returns:
        Encoded JWT token string.

    Example claims:
        {
            "sub": "user-uuid",
            "email": "user@example.com",
            "org_id": "org-uuid",
            "roles": ["ORG_ADMIN"]
        }
    """
    if ttl_min is None:
        ttl_min = settings.AUTH_ACCESS_TTL_MIN

    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=ttl_min)

    to_encode = claims.copy()
    to_encode.update(
        {
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.AUTH_SECRET,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT access token.

    Args:
        token: JWT token string to decode.

    Returns:
        Dictionary of claims from the token.

    Raises:
        JWTError: If token is invalid, expired, or signature verification fails.
    """
    try:
        payload = jwt.decode(
            token,
            settings.AUTH_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}") from e
