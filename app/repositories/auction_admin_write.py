from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from app.schemas.auctions import Auction


class AuctionAdminWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        *,
        id: int | None,
        product_id: int,
        start_price: float,
        min_bid_price: float,
        buy_now_price: float | None,
        deposit_amount: float,
        starts_at: datetime,
        ends_at: datetime,
        status: str,
    ) -> Auction:
        if id:
            auction = self.db.get(Auction, id)
            if not auction:
                auction = Auction(id=id)
                self.db.add(auction)
        else:
            auction = self.db.execute(select(Auction).where(Auction.product_id == product_id)).scalar_one_or_none()
            if not auction:
                auction = Auction(product_id=product_id)
                self.db.add(auction)
        auction.product_id = product_id
        auction.start_price = start_price
        auction.min_bid_price = min_bid_price
        auction.buy_now_price = buy_now_price
        auction.deposit_amount = deposit_amount
        auction.starts_at = starts_at
        auction.ends_at = ends_at
        auction.status = status
        self.db.flush()
        return auction

    def update_status(self, auction_id: int, status: str) -> None:
        a = self.db.get(Auction, auction_id)
        if a:
            a.status = status
            self.db.flush()

