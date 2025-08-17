from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Auction(Base):
    __tablename__ = "auction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(
        BigInteger, ForeignKey("product.id"), nullable=False, unique=True
    )
    start_price = Column(DECIMAL(12, 2), nullable=False)
    min_bid_price = Column(DECIMAL(12, 2), nullable=False)
    buy_now_price = Column(DECIMAL(12, 2))
    deposit_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    status = Column(String(10), nullable=False, default="SCHEDULED")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    product = relationship("Product", backref="auction", uselist=False)
