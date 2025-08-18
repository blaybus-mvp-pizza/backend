from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey
from app.db.session import Base


class ProductImage(Base):
    __tablename__ = "product_image"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("product.id"), nullable=False)
    image_type = Column(String(10), nullable=False)
    image_url = Column(String(1024), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
