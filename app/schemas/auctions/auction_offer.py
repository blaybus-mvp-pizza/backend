from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class AuctionOffer(Base):
    __tablename__ = "auction_offer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    auction_id = Column(BigInteger, ForeignKey("auction.id"), nullable=False)
    bid_id = Column(BigInteger, ForeignKey("bid.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    rank_order = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    offered_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    order_id = Column(BigInteger)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
