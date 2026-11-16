import hashlib
from datetime import UTC, datetime, timedelta

import jwt

from packages.core.config import get_settings

settings = get_settings()


class AccessDeniedError(Exception):
    pass


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Multi-tenant user directory with roles and workspace authorizations
USER_DIRECTORY = {
    "alice": {"role": "admin", "workspaces": ["hr-docs", "api-docs", "engineering"]},
    "bob": {"role": "viewer", "workspaces": ["api-docs"]},
    "charlie": {"role": "editor", "workspaces": ["engineering"]},
}

# User credentials repository (in production, backed by PostgreSQL or OAuth/OIDC IdP)
USER_CREDENTIALS = {
    "alice": {
        "password_hash": hash_password("password123"),
        "role": "admin",
        "workspaces": ["hr-docs", "api-docs", "engineering"],
    },
    "bob": {
        "password_hash": hash_password("password123"),
        "role": "viewer",
        "workspaces": ["api-docs"],
    },
    "charlie": {
        "password_hash": hash_password("password123"),
        "role": "editor",
        "workspaces": ["engineering"],
    },
}


def authenticate_user(username: str, password: str) -> dict | None:
    """Validate username and password, returning user claims or None."""
    user = USER_CREDENTIALS.get(username)
    if not user:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return {
        "user_id": username,
        "role": user["role"],
        "workspaces": user["workspaces"],
    }


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT access token containing subject, role, and workspaces."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT access token, enforcing signature and expiration."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AccessDeniedError("JWT token has expired")
    except jwt.InvalidTokenError as e:
        raise AccessDeniedError(f"Invalid JWT token: {e!s}")


def assert_workspace_access(user_id: str, workspace_id: str):
    user_record = USER_DIRECTORY.get(user_id)
    if not user_record or workspace_id not in user_record["workspaces"]:
        raise AccessDeniedError(f"User '{user_id}' is not authorized to access workspace '{workspace_id}'")


def assert_can_write(user_id: str, workspace_id: str):
    assert_workspace_access(user_id, workspace_id)
    role = USER_DIRECTORY[user_id]["role"]
    if role not in {"admin", "editor"}:
        raise AccessDeniedError(f"User '{user_id}' lacks write permissions for workspace '{workspace_id}'")
