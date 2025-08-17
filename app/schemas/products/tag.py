from sqlalchemy import Column, Integer, String
from app.db.session import Base


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(60), nullable=False, unique=True)
