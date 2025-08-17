from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class Shipment(Base):
    __tablename__ = "shipment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, nullable=False)
    courier_name = Column(String(60), nullable=False)
    tracking_number = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PREPARING")
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
