from datetime import datetime, timezone
from sqlalchemy import select
from app.infrastructure.db.uow import SqlAlchemyUnitOfWork
from app.domains.auctions.enums import AuctionStatus
from app.schemas.auctions import Auction


class AuctionScheduleBatch:
    def run_once(self):
        with SqlAlchemyUnitOfWork() as uow:
            now = datetime.now(timezone.utc)
            stmt = select(Auction).where(
                Auction.status == AuctionStatus.SCHEDULED.value,
                Auction.starts_at <= now,
            )
            for row in uow.session.execute(stmt):
                auction: Auction = row[0]
                if auction.ends_at > now:
                    auction.status = AuctionStatus.RUNNING.value
            uow.session.flush()


