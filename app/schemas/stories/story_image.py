from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey, DateTime
from app.db.session import Base
from sqlalchemy.sql import func


class StoryImage(Base):
    __tablename__ = "story_image"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    story_id = Column(BigInteger, ForeignKey("story.id"), nullable=False)
    image_url = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
