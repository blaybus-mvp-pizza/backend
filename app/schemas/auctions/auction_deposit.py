from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    DECIMAL,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.sql import func
from app.db.session import Base


class AuctionDeposit(Base):
    __tablename__ = "auction_deposit"
    __table_args__ = (
        UniqueConstraint("auction_id", "user_id", name="uq_deposit_user_auction"),
        Index("idx_ad_auction", "auction_id"),
        Index("idx_ad_user", "user_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    auction_id = Column(BigInteger, ForeignKey("auction.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    payment_id = Column(BigInteger)
    amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(String(10), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
