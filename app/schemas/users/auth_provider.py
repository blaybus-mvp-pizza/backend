from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    String,
    func,
)

from app.db.session import Base


class AuthProvider(Base):
    __tablename__ = "auth_provider"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    provider = Column(String(10), nullable=False)
    provider_user_id = Column(String(191), nullable=False)
    email = Column(String(255), nullable=True)
    raw_profile_json = Column(JSON, nullable=True)

    linked_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint(provider, provider_user_id),)
