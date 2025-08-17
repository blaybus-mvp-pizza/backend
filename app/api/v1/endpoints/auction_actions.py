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

        @self.router.post("/bid", response_model=BidResult)
        async def bid(
            auction_id: int,
            amount: float,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id),
        ):
            return service.place_bid(
                auction_id=auction_id, amount=amount, user_id=user_id
            )

        @self.router.post("/buy-now", response_model=BuyNowResult)
        async def buy_now(
            auction_id: int,
            service: AuctionService = Depends(get_auction_service),
            user_id: int = Depends(get_current_user_id),
        ):
            return service.buy_now(auction_id=auction_id, user_id=user_id)


api = AuctionAPI().router
