from sqlalchemy.orm import Session
from app.core.errors import BusinessError
from app.core.error_codes import ErrorCode
from app.repositories.auction_read import AuctionReadRepository
from app.repositories.auction_write import AuctionWriteRepository
from app.domains.auctions.bid_rules import BidRules
from app.domains.auctions.enums import AuctionStatus


class BidVerificator:
    def __init__(self, db: Session):
        self.db = db
        self.read = AuctionReadRepository(db)
        self.write = AuctionWriteRepository(db)

    # 경매가 활성 상태인지 확인
    def ensure_auction_running(self, auction_id: int):
        auction = self.write.get_auction_by_id(auction_id)

        if not auction:
            print('ensure_auction_running',auction)
            raise BusinessError(ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다.")
        if auction.status != AuctionStatus.RUNNING.value:
            raise BusinessError(ErrorCode.AUCTION_NOT_RUNNING, "경매가 활성 상태가 아닙니다.")
        return auction

    def ensure_not_already_bid(self, auction_id: int, user_id: int):
        bid = self.read.get_bid_by_auction_and_user(auction_id, user_id)
        if bid:
            raise BusinessError(ErrorCode.BID_ALREADY_EXISTS, "이미 참여한 경매입니다.")

    def ensure_auction_exists_and_running(self, auction_id: int):
        auction = self.write.get_auction_by_id(auction_id)

        if not auction:
            raise BusinessError(ErrorCode.AUCTION_NOT_FOUND, "경매를 찾을 수 없습니다.")
        if auction.status != AuctionStatus.RUNNING.value:
            raise BusinessError(
                ErrorCode.BID_NOT_ALLOWED, "경매가 활성 상태가 아닙니다."
            )
        return auction

    def ensure_amount_allowed(self, *, auction_product_id: int, amount: float):
        info = self.read.get_auction_info_by_product(auction_product_id)
        if not info:
            raise BusinessError(
                ErrorCode.AUCTION_NOT_FOUND, "경매 정보를 찾을 수 없습니다."
            )
        current = (
            float(info.current_highest_bid)
            if info.current_highest_bid is not None
            else float(info.min_bid_price)
        )
        buy_now = float(info.buy_now_price) if info.buy_now_price is not None else None
        steps = BidRules.make_bid_steps(current, buy_now, count=100)
        # allow equality tolerance due to float -> DECIMAL conversions
        if all(abs(float(amount) - float(s)) > 0.1 for s in steps):
            raise BusinessError(
                ErrorCode.BID_NOT_ALLOWED, "입찰 가능한 금액이 아닙니다."
            )
        return float(info.deposit_amount or 0)

    def verify_buy_now(self, auction):
        if auction.status != AuctionStatus.RUNNING.value:
            raise BusinessError(
                ErrorCode.BUY_NOT_ALLOWED, "경매가 활성 상태가 아닙니다."
            )
        if not auction.buy_now_price:
            raise BusinessError(
                ErrorCode.BUY_NOT_ALLOWED, "즉시구매가 설정되어 있지 않습니다."
            )
