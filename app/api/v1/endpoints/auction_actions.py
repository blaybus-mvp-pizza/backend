from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id
from app.domains.auctions.service import AuctionService
from app.domains.auctions.bid_result import BidResult
from app.domains.auctions.buy_now_result import BuyNowResult
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.repositories.order_write import OrderWriteRepository
from app.repositories.payment_write import PaymentWriteRepository
from app.repositories.notification_write import NotificationWriteRepository


def get_auction_service(db: Session = Depends(get_db)) -> AuctionService:
    return AuctionService(
        db,
        AuctionReadRepository(db),
        AuctionWriteRepository(db),
        OrderWriteRepository(db),
        PaymentWriteRepository(db),
        NotificationWriteRepository(db),
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
        )
        async def bid(
            auction_id: int,
            amount: float,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id),
        ):
            return service.place_bid(
                auction_id=auction_id, amount=amount, user_id=user_id
            )

        @self.router.post(
            "/buy-now",
            response_model=BuyNowResult,
            summary="즉시구매",
            description="즉시구매 가격으로 주문과 결제를 한 번에 처리합니다.",
            response_description="즉시구매 결과",
        )
        async def buy_now(
            auction_id: int,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id),
        ):
            return service.buy_now(auction_id=auction_id, user_id=user_id)


api = AuctionAPI().router
