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
from app.domains.auth.models import Login_url, Token
from app.domains.users.service import UserService
from app.repositories.user_read import UserReadRepository
from app.repositories.user_write import UserWriteRepository


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db, UserReadRepository(db), UserWriteRepository(db))


class AuthAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/login/google/login-url",
            response_model=Login_url,
            response_description="구글 로그인 URL 포함한 body",
            summary="Authenticate user for Google login",
            description="구글 소셜 로그인 시 사용할 URL을 반환합니다. 해당 URL로 이동 시 로그인 후 얻은 code와 함께 /user/v1/auth/login/google/callback로 리다이렉션됩니다.",
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
            return Login_url(login_url=redirect_url)

        @self.router.get(
            "/login/google/callback",
            response_model=Token,
            response_description="토큰 포함한 body",
            summary="Handle Google OAuth callback and issue JWT token",
            description="구글 소셜 로그인 후 리다이렉션되는 콜백 URL입니다. 이 엔드포인트는 Google OAuth 인증 후 받은 code를 사용하여 JWT 토큰을 발급합니다.",
        )
        async def google_callback(
            code: str, service: UserService = Depends(get_user_service)
        ) -> Token:
            if not code:
                raise HTTPException(
                    status_code=400, detail="Missing authorization code"
                )

            id_token = await get_google_id_token(code)
            if not id_token:
                raise HTTPException(
                    status_code=400, detail="Failed to obtain Google ID token"
                )
            id_info = verify_google_id_token(id_token)
            if not id_info:
                raise HTTPException(status_code=400, detail="Invalid Google ID token")

            try:
                user = service.signup_user_with_oauth(
                    email=id_info.get("email"),
                    nickname=id_info.get("name"),
                    provider=PROVIDER_TYPE.GOOGLE,
                    provider_user_id=id_info["sub"],
                    raw_profile_json=id_info,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            token = create_access_token(subject=str(user.id))
            redirect_url = f"{settings.FRONTEND_REDIRECT_URL}?access_token={token}"
            response = RedirectResponse(
                url=redirect_url,
                status_code=status.HTTP_302_FOUND,
            )
            return response


api = AuthAPI().router
