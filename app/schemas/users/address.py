from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, func

from app.db.session import Base


class Address(Base):
    __tablename__ = "address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)

    recipient_name = Column(String(60), nullable=False)
    phone_e164 = Column(String(20), nullable=False)
    postcode = Column(String(10), nullable=True)
    address1 = Column(String(255), nullable=False)
    address2 = Column(String(255), nullable=True)

    is_default = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
