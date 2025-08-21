from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.deps import get_db
from app.repositories.user_read import UserReadRepository
from app.core.config import settings


def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    token = authorization.split(" ", 1)[1].strip()
    # Try JWT first
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is not None:
            return int(sub)
    except Exception:
        pass
    # Fallback: token itself is integer user id
    try:
        return int(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user_id_verified(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> int:
    """Resolve the current user id from the Authorization header and ensure the user exists.

    Returns 401 if the token is missing/invalid or if the user does not exist.
    """
    user_id = get_current_user_id(authorization)
    user = UserReadRepository(db).get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user_id


def require_admin(authorization: Optional[str] = Header(None)) -> None:
    """Admin token based authorization.

    - Accepts static admin token via Authorization: Bearer <token>
    - Returns 401 if missing/invalid
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    token = authorization.split(" ", 1)[1].strip()
    if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token"
        )
    return None
