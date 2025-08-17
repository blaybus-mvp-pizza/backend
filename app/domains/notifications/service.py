from sqlalchemy.orm import Session
from app.repositories.notification_write import NotificationWriteRepository
from app.domains.notifications.dto import NotifyRequest, NotifyResult


class NotificationService:
    def __init__(self, db: Session, repo: NotificationWriteRepository | None = None):
        self.db = db
        self.repo = repo or NotificationWriteRepository(db)

    def send(self, req: NotifyRequest) -> NotifyResult:
        """알림 기록 생성 (MVP)

        :param req: 알림 요청 DTO
        :return: NotifyResult(ok)
        """
        self.repo.create(
            user_id=req.user_id, title=req.title, body=req.body, channel=req.channel
        )
        return NotifyResult(ok=True)
