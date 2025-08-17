from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    String,
    Boolean,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.db.session import Base


class PaymentMethod(Base):
    __tablename__ = "payment_method"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)

    provider = Column(String(10), nullable=False)
    external_key = Column(String(191), nullable=False)
    masked_info = Column(String(191), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint(user_id, provider, external_key),)
