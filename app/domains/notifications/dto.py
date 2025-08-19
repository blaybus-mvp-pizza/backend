from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NotifyRequest(BaseModel):
    user_id: int
    title: str
    body: str
    channel: str = "PUSH"


class NotifyResult(BaseModel):
    ok: bool = True


class NotificationItem(BaseModel):
    id: int
    title: str
    body: str
    sent_at: datetime
    status: str


class NotificationListResult(BaseModel):
    items: List[NotificationItem]


class MarkReadRequest(BaseModel):
    notification_ids: List[int]


class MarkReadResult(BaseModel):
    ok: bool = True
