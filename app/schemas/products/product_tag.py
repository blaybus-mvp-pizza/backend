from sqlalchemy import Column, BigInteger, Integer, ForeignKey
from app.db.session import Base


class ProductTag(Base):
    __tablename__ = "product_tag"

    product_id = Column(BigInteger, ForeignKey("product.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True)
