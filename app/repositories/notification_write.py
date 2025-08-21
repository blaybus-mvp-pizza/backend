from sqlalchemy.orm import Session
from app.schemas.notifications import Notification


class NotificationWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, user_id: int | None, title: str, body: str, channel: str = "PUSH", product_id: int | None = None
    ) -> Notification:
        n = Notification(
            user_id=user_id, title=title, body=body, channel=channel, status="SENT", product_id=product_id
        )
        self.db.add(n)
        self.db.commit()
        self.db.refresh(n)
        return n
