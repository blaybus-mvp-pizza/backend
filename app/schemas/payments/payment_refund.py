from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.db.session import Base


class PaymentRefund(Base):
    __tablename__ = "payment_refund"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_id = Column(BigInteger, nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    reason = Column(String(255))
    refunded_at = Column(DateTime, nullable=False, server_default=func.now())
