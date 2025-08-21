from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id_verified
from app.domains.auctions.service import AuctionService
from app.domains.auctions.bid_result import BidResult
from app.domains.auctions.buy_now_result import BuyNowResult
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.domains.notifications.service import NotificationService
from app.repositories.auction_deposit import AuctionDepositRepository
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.auctions.service import AuctionService as AuctionDomainService


def get_auction_service(db: Session = Depends(get_db)) -> AuctionService:
    return AuctionService(
        db,
        AuctionReadRepository(db),
        AuctionWriteRepository(db),
        OrderWriteRepository(db),
        PaymentWriteRepository(db),
        AuctionDepositRepository(db),
        NotificationService(db),
    )


class AuctionAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.post(
            "/bid",
            response_model=BidResult,
            summary="입찰하기",
            description="현재 진행중인 경매에 입찰합니다. 필요 시 보증금이 결제됩니다.",
            response_description="입찰 결과",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                    "content": {
                        "application/json": {
                            "examples": {
                                "BID_ALREADY_EXISTS": {
                                    "summary": "이미 입찰한 경매",
                                    "value": {
                                        "code": "BID_ALREADY_EXISTS",
                                        "message": "이미 입찰한 경매입니다.",
                                    },
                                },
                                "AUCTION_NOT_RUNNING": {
                                    "summary": "경매 진행 중이 아님",
                                    "value": {
                                        "code": "AUCTION_NOT_RUNNING",
                                        "message": "경매가 진행 중이 아닙니다.",
                                    },
                                },
                                "AUCTION_NOT_FOUND": {
                                    "summary": "경매 없음",
                                    "value": {
                                        "code": "AUCTION_NOT_FOUND",
                                        "message": "경매를 찾을 수 없습니다.",
                                    },
                                },
                                "BID_NOT_ALLOWED": {
                                    "summary": "입찰 불가(금액/상태)",
                                    "value": {
                                        "code": "BID_NOT_ALLOWED",
                                        "message": "입찰할 수 없습니다.",
                                    },
                                },
                            }
                        }
                    },
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def bid(
            auction_id: int,
            amount: float,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id_verified),
        ):
            # normalize amount to float explicitly
            print('request ', auction_id)
            return service.place_bid(
                auction_id=auction_id, amount=float(amount), user_id=user_id
            )

        @self.router.post(
            "/buy-now",
            response_model=BuyNowResult,
            summary="즉시구매",
            description="즉시구매 가격으로 주문과 결제를 한 번에 처리합니다.",
            response_description="즉시구매 결과",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                    "content": {
                        "application/json": {
                            "examples": {
                                "AUCTION_NOT_FOUND": {
                                    "summary": "경매 없음",
                                    "value": {
                                        "code": "AUCTION_NOT_FOUND",
                                        "message": "경매를 찾을 수 없습니다.",
                                    },
                                },
                                "BUY_NOT_ALLOWED": {
                                    "summary": "즉시구매 불가(상태/가격)",
                                    "value": {
                                        "code": "BUY_NOT_ALLOWED",
                                        "message": "즉시구매를 진행할 수 없습니다.",
                                    },
                                },
                            }
                        }
                    },
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def buy_now(
            auction_id: int,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id_verified),
        ):
            return service.buy_now(auction_id=auction_id, user_id=user_id)

        # finalize endpoint moved to admin router


api = AuctionAPI().router
