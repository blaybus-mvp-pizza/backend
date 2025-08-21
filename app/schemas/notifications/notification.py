from sqlalchemy import Column, BigInteger, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class Notification(Base):
    __tablename__ = "notification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    channel = Column(String(20), nullable=False, default="PUSH")
    product_id = Column(BigInteger)
    template_code = Column(String(80))
    title = Column(String(200))
    body = Column(String(1024))
    metadata_json = Column(JSON)
    sent_at = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String(20), nullable=False, default="SENT")
