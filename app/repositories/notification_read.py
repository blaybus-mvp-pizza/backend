from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.schemas.notifications import Notification


class NotificationReadRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, *, user_id: int, limit: int = 50) -> List[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.sent_at))
            .limit(limit)
        )
        return [row[0] for row in self.db.execute(stmt).all()]


