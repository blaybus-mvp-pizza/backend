from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.core.auth_deps import get_current_user_id_verified
from app.domains.notifications.service import NotificationService
from app.domains.notifications.dto import (
    NotificationListResult,
    MarkReadRequest,
    MarkReadResult,
    UnreadCountResult,
)
from app.domains.common.error_response import ServerErrorResponse


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


class NotificationsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "",
            response_model=NotificationListResult,
            summary="내 알림 목록",
            description="최신순으로 정렬된 내 알림을 조회합니다.",
            response_description="알림 리스트",
            responses={500: {"model": ServerErrorResponse, "description": "서버 내부 오류"}},
        )
        async def list_notifications(
            limit: int = Query(50, ge=1, le=200),
            service: NotificationService = Depends(get_notification_service),
            user_id: int = Depends(get_current_user_id_verified),
        ):
            return service.list_my_notifications(user_id=user_id, limit=limit)

        @self.router.post(
            "/read",
            response_model=MarkReadResult,
            summary="알림 읽음 처리",
            description="알림 id 리스트를 받아 상태를 READ로 변경합니다.",
            response_description="처리 결과",
            responses={500: {"model": ServerErrorResponse, "description": "서버 내부 오류"}},
        )
        async def mark_read(
            req: MarkReadRequest,
            service: NotificationService = Depends(get_notification_service),
            user_id: int = Depends(get_current_user_id_verified),
        ):
            # 간단히 상태 업데이트. 소유권 검증은 추후 확장 가능
            return service.mark_read(req)

        @self.router.get(
            "/count/unread",
            response_model=UnreadCountResult,
            summary="안읽은 알림 개수",
            description="현재 사용자의 안읽은 알림 개수를 반환합니다.",
            response_description="카운트",
            responses={500: {"model": ServerErrorResponse, "description": "서버 내부 오류"}},
        )
        async def unread_count(
            service: NotificationService = Depends(get_notification_service),
            user_id: int = Depends(get_current_user_id_verified),
        ):
            return service.unread_count(user_id=user_id)


api = NotificationsAPI().router


