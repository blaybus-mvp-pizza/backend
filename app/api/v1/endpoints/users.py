from fastapi import APIRouter, Depends, HTTPException, Header, status
from requests import Session

from app.core.deps import get_db
from app.core.errors import BusinessError
from app.core.security import require_auth
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.users.models import (
    PhoneVerificationResult,
    SendSMSResult,
    UserRead,
    UserUpdate,
)
from app.domains.users.service import UserService
from app.repositories.user_read import UserReadRepository
from app.repositories.user_write import UserWriteRepository


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db, UserReadRepository(db), UserWriteRepository(db))


class UsersAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/me",
            response_model=UserRead,
            response_description="현재 유저 정보",
            summary="[required auth] Get current user",
            description="현재 로그인 한 사용자의 정보를 반환합니다.",
        )
        async def get_current_user(
            user_id: int = Depends(require_auth),
            service: UserService = Depends(get_user_service),
        ) -> UserRead:
            current_user = service.get_user_info(user_id=user_id)
            if not current_user:
                raise HTTPException(status_code=404, detail="User not found")
            return current_user

        @self.router.put(
            "/me",
            response_model=UserRead,
            response_description="수정된 현재 유저 정보",
            summary="[required auth] Update current user",
            description="현재 로그인 한 사용자의 정보를 업데이트합니다. 핸드폰번호 변경 시 핸드폰 인증 여부를 확인합니다.",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                404: {
                    "model": BusinessErrorResponse,
                    "description": "유저를 찾을 수 없음",
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def update_current_user(
            user_data: UserUpdate,
            user_id: int = Depends(require_auth),
            service: UserService = Depends(get_user_service),
        ) -> UserRead:
            user = service.update_user_info(user_id=user_id, user_data=user_data)
            if not user:
                raise BusinessError(status_code=404, detail="User not found")
            return user

        @self.router.post(
            "/me/phone-verification-sms",
            response_model=SendSMSResult,
            summary="[required auth] Request phone verification SMS",
            description="휴대폰번호로 인증 SMS를 요청합니다. ",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def request_phone_verification_sms(
            phone_number: str,
            user_id: int = Depends(require_auth),
            service: UserService = Depends(get_user_service),
        ) -> SendSMSResult:
            return service.send_phone_verification_sms(
                user_id=user_id, phone_number=phone_number
            )

        @self.router.post(
            "/me/phone-verification-sms/verify",
            response_model=PhoneVerificationResult,
            summary="[required auth] Verify phone verification SMS",
            description="인증 SMS로 받은 인증 코드를 검증합니다.",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def verify_phone_verification_sms(
            phone_number: str,
            code6: str,
            user_id: int = Depends(require_auth),
            service: UserService = Depends(get_user_service),
        ) -> PhoneVerificationResult:
            return service.verify_phone_verification_sms(
                phone_number=phone_number,
                code6=code6,
                user_id=user_id,
            )


api = UsersAPI().router
