from nt import access
from tkinter import PROJECTING
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.deps import get_db
from app.core.security import (
    create_access_token,
    get_google_id_token,
    verify_google_id_token,
)
from app.domains.auth.enum import PROVIDER_TYPE
from app.domains.users.service import (
    signup_user_with_oauth,
)
from app.domains.users.models import UserCreate
from app.domains.auth.models import Token

router = APIRouter()


@router.get(
    "/login/google/login-url",
    summary="Authenticate user for Google login",
)
async def login_google() -> str:
    google_auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = "openid email profile"
    response_type = "code"

    redirect_url = (
        f"{google_auth_endpoint}"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type={response_type}"
        f"&scope={scope}"
    )
    return redirect_url


@router.get(
    "/login/google/callback",
    response_model=Token,
    summary="Handle Google OAuth callback and issue JWT token",
)
async def google_callback(code: str, db: Session = Depends(get_db)) -> Token:
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    id_token = await get_google_id_token(code)
    if not id_token:
        raise HTTPException(status_code=400, detail="Failed to obtain Google ID token")
    id_info = verify_google_id_token(id_token)
    if not id_info:
        raise HTTPException(status_code=400, detail="Invalid Google ID token")

    try:
        user = signup_user_with_oauth(
            db,
            email=id_info.get("email"),
            nickname=id_info.get("name"),
            provider=PROVIDER_TYPE.GOOGLE,
            provider_user_id=id_info["sub"],
            raw_profile_json=id_info,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token(subject=str(user.id))
    # response = RedirectResponse(
    #     url="http://localhost:3000", status_code=status.HTTP_302_FOUND
    # )
    # response.set_cookie(key="access_token", value=token, httponly=True, secure=True)
    # return response
    return Token(access_token=token)
