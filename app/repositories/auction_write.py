from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.schemas.auctions import Auction, Bid


class AuctionWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def user_has_bid(self, auction_id: int, user_id: int) -> bool:
        stmt = select(func.count(Bid.id)).where(
            Bid.auction_id == auction_id, Bid.user_id == user_id
        )
        return self.db.execute(stmt).scalar_one() > 0

    def get_auction_by_id(self, auction_id: int) -> Auction | None:
        print('get auction', auction_id)
        return self.db.execute(
            select(Auction).where(Auction.id == auction_id)
        ).scalar_one_or_none()

    def place_bid(self, auction_id: int, user_id: int, amount: float) -> Bid:
        last_order = self.db.execute(
            select(func.max(Bid.bid_order)).where(Bid.auction_id == auction_id)
        ).scalar_one()
        next_order = (last_order or 0) + 1
        bid = Bid(
            auction_id=auction_id, user_id=user_id, amount=amount, bid_order=next_order
        )
        self.db.add(bid)
        self.db.commit()
        self.db.refresh(bid)
        return bid
