from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.domains.common.base_model import BaseResponseModel


class NotifyRequest(BaseModel):
    user_id: int
    title: str
    body: str
    channel: str = "PUSH"
    product_id: int | None = None


class NotifyResult(BaseModel):
    ok: bool = True


class NotificationItem(BaseResponseModel):
    id: int
    title: str
    body: str
    sent_at: datetime
    status: str
    image_url: str | None = None


class NotificationListResult(BaseModel):
    items: List[NotificationItem]


class MarkReadRequest(BaseModel):
    notification_ids: List[int]


class MarkReadResult(BaseModel):
    ok: bool = True


class UnreadCountResult(BaseModel):
    count: int
