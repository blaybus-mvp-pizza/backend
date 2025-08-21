from sqlalchemy.orm import Session
from app.repositories.notification_write import NotificationWriteRepository
from app.repositories.notification_read import NotificationReadRepository
from app.domains.notifications.dto import (
    NotifyRequest,
    NotifyResult,
    NotificationListResult,
    NotificationItem,
    MarkReadRequest,
    MarkReadResult,
    UnreadCountResult,
)
from app.schemas.products import ProductImage


class NotificationService:
    def __init__(self, db: Session, repo: NotificationWriteRepository | None = None):
        self.db = db
        self.repo = repo or NotificationWriteRepository(db)
        self.read = NotificationReadRepository(db)

    def send(self, req: NotifyRequest) -> NotifyResult:
        """알림 기록 생성 (MVP)

        :param req: 알림 요청 DTO
        :return: NotifyResult(ok)
        """
        self.repo.create(
            user_id=req.user_id, title=req.title, body=req.body, channel=req.channel, product_id=req.product_id
        )
        return NotifyResult(ok=True)

    def list_my_notifications(self, *, user_id: int, limit: int = 50) -> NotificationListResult:
        notifications = self.read.list_by_user(user_id=user_id, limit=limit)
        items = []
        for n in notifications:
            image_url = None
            if n.product_id:
                row = self.db.execute(
                    select(ProductImage.image_url)
                    .where(ProductImage.product_id == n.product_id)
                    .order_by(ProductImage.sort_order.asc())
                    .limit(1)
                ).first()
                if row:
                    image_url = row[0]
            items.append(
                NotificationItem(
                    id=int(n.id),
                    title=n.title or "",
                    body=n.body or "",
                    sent_at=n.sent_at,
                    status=n.status,
                    image_url=image_url,
                )
            )
        return NotificationListResult(items=items)

    def mark_read(self, req: MarkReadRequest) -> MarkReadResult:
        # 단순 업데이트: 상태를 READ로 변경
        from sqlalchemy import update
        from app.schemas.notifications import Notification

        if not req.notification_ids:
            return MarkReadResult(ok=True)
        stmt = (
            update(Notification)
            .where(Notification.id.in_(req.notification_ids))
            .values(status="READ")
        )
        self.db.execute(stmt)
        self.db.commit()
        return MarkReadResult(ok=True)

    def unread_count(self, *, user_id: int) -> UnreadCountResult:
        cnt = self.read.count_unread_by_user(user_id=user_id)
        return UnreadCountResult(count=cnt)
