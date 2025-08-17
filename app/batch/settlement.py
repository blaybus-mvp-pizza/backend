from sqlalchemy.orm import Session
from app.batch.auction_settlement import AuctionSettlementBatch


def run(db: Session):
    batch = AuctionSettlementBatch(db)
    batch.run_once()
