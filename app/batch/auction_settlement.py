from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from app.schemas.auctions import Auction, Bid
from app.domains.auctions.enums import AuctionStatus
from app.repositories.auction_deposit import AuctionDepositRepository
from app.domains.payments.service import PaymentService
from app.domains.payments.dto import RefundRequest
from app.domains.notifications.service import NotificationService
from app.domains.notifications.dto import NotifyRequest


class AuctionSettlementBatch:
    def __init__(self, db: Session):
        self.db = db
        self.deposits = AuctionDepositRepository(db)
        self.payments = PaymentService(db)
        self.notifications = NotificationService(db)

    def run_once(self):
        stmt = select(Auction).where(
            Auction.status == AuctionStatus.RUNNING.value,
            Auction.ends_at <= datetime.now(timezone.utc),
        )
        for row in self.db.execute(stmt):
            auction = row[0]
            self._settle_auction(auction)

    def _settle_auction(self, auction: Auction):
        winner_row = self.db.execute(
            select(Bid)
            .where(Bid.auction_id == auction.id)
            .order_by(Bid.amount.desc(), Bid.created_at.desc())
            .limit(1)
        ).first()
        if not winner_row:
            auction.status = AuctionStatus.ENDED.value
            self.db.commit()
            return
        winner: Bid = winner_row[0]
        for dep in self.deposits.list_by_auction(auction.id):
            if (
                dep.user_id != winner.user_id
                and dep.status != "REFUNDED"
                and dep.payment_id
            ):
                self.payments.refund(
                    RefundRequest(payment_id=dep.payment_id, amount=float(dep.amount))
                )
                self.deposits.mark_refunded(dep.id)
        self.db.commit()
        self.notifications.send(
            NotifyRequest(
                user_id=winner.user_id,
                title=f"{auction.product.name}",
                body="낙찰되었습니다. 결제를 진행해 주세요.",
            )
        )
        auction.status = AuctionStatus.ENDED.value
        self.db.commit()
