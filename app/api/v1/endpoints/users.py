from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.errors import BusinessError
from app.core.security import require_auth
from app.domains.common.paging import Page
from app.domains.auctions.user_dto import UserAuctionDashboard, UserRelatedAuctionItem
from app.domains.auctions.user_service import UserAuctionService
from app.repositories.user_auction_read import UserAuctionReadRepository
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


def get_user_auction_service(db: Session = Depends(get_db)) -> UserAuctionService:
    return UserAuctionService(db, UserAuctionReadRepository(db))


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

        @self.router.get(
            "/me/auctions/dashboard",
            response_model=UserAuctionDashboard,
            summary="마이페이지 경매 대시보드 카운트",
            description="로그인 사용자의 경매 참여 현황 카운트를 반환합니다.",
        )
        async def my_auction_dashboard(
            user_id: int = Depends(require_auth),
            service: UserAuctionService = Depends(get_user_auction_service),
        ) -> UserAuctionDashboard:
            return service.dashboard(user_id=user_id)

        @self.router.get(
            "/me/auctions",
            response_model=Page[UserRelatedAuctionItem],
            summary="마이페이지 관련 상품 조회",
            description="로그인 사용자의 관련 상품(입찰/낙찰 등)을 페이징 조회합니다.",
        )
        async def my_related_auctions(
            user_id: int = Depends(require_auth),
            service: UserAuctionService = Depends(get_user_auction_service),
            page: int = Query(1, ge=1),
            size: int = Query(10, ge=1, le=100),
            period: str = Query("1m", description="기간: 1m|3m|custom"),
            startDate: str | None = Query(None, description="custom 시작일(ISO)"),
            endDate: str | None = Query(None, description="custom 종료일(ISO)"),
            q: str | None = Query(None, description="검색 키워드: 상품명 or 브랜드명"),
        ) -> Page[UserRelatedAuctionItem]:
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            period_from = None
            period_to = None
            try:
                if period == "1m":
                    period_from = now - timedelta(days=30)
                    period_to = now
                elif period == "3m":
                    period_from = now - timedelta(days=90)
                    period_to = now
                elif period == "custom" and startDate and endDate:
                    period_from = datetime.fromisoformat(startDate)
                    period_to = datetime.fromisoformat(endDate)
            except Exception:
                period_from, period_to = None, None
            return service.list_related(
                user_id=user_id,
                page=page,
                size=size,
                period_from=period_from,
                period_to=period_to,
                keyword=q,
            )


api = UsersAPI().router
