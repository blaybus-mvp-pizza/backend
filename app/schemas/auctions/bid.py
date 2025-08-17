from sqlalchemy import Column, BigInteger, Integer, DateTime, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Bid(Base):
    __tablename__ = "bid"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    auction_id = Column(BigInteger, ForeignKey("auction.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    bid_order = Column(Integer, nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    auction = relationship("Auction", backref="bids")
