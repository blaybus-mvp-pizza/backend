from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class Order(Base):
    __tablename__ = "order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    address_id = Column(BigInteger)
    status = Column(String(20), nullable=False, default="PENDING")
    total_amount = Column(Integer, nullable=False, default=0)
    shipping_fee = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
