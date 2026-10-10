"""Authentication helpers for future control endpoints."""

import os
import secrets

from fastapi import Header, HTTPException, status

TOKEN_ENVIRONMENT_VARIABLE = "CHAOSCOMMS_API_TOKEN"


def control_authentication_configured() -> bool:
    return bool(os.environ.get(TOKEN_ENVIRONMENT_VARIABLE))


def require_control_token(authorization: str | None = Header(default=None)) -> None:
    configured = os.environ.get(TOKEN_ENVIRONMENT_VARIABLE)
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="control authentication is not configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    supplied = authorization.removeprefix("Bearer ")
    if not supplied or not secrets.compare_digest(supplied, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
