from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.auctions import AuctionDeposit


class AuctionDepositRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        auction_id: int,
        user_id: int,
        payment_id: int,
        amount: float,
        status: str = "PAID"
    ) -> AuctionDeposit:
        rec = AuctionDeposit(
            auction_id=auction_id,
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            status=status,
        )
        self.db.add(rec)
        self.db.flush()
        return rec

    def list_by_auction(self, auction_id: int):
        stmt = select(AuctionDeposit).where(AuctionDeposit.auction_id == auction_id)
        return [row[0] for row in self.db.execute(stmt)]

    def mark_refunded(self, deposit_id: int):
        rec = self.db.get(AuctionDeposit, deposit_id)
        if rec:
            rec.status = "REFUNDED"
            self.db.flush()
