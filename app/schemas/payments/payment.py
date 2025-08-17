from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    DateTime,
    DECIMAL,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.sql import func
from app.db.session import Base


class Payment(Base):
    __tablename__ = "payment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger)
    user_id = Column(BigInteger, nullable=False)
    provider = Column(String(30), nullable=False)
    external_tid = Column(String(191))
    amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    requested_at = Column(DateTime, nullable=False, server_default=func.now())
    paid_at = Column(DateTime)
    fail_reason = Column(String(255))
