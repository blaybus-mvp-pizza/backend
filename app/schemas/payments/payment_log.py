from sqlalchemy import Column, BigInteger, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class PaymentLog(Base):
    __tablename__ = "payment_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_id = Column(BigInteger, nullable=False)
    provider = Column(String(30), nullable=False)
    external_tid = Column(String(191))
    amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    requested_at = Column(DateTime, nullable=False, server_default=func.now())
    paid_at = Column(DateTime)
    fail_reason = Column(String(255))
    log_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
