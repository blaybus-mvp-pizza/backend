from fastapi import Header, HTTPException, status
from typing import Optional
from app.core.security import decode_access_token


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
