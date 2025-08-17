from pydantic import BaseModel
from typing import Optional


class NotifyRequest(BaseModel):
    user_id: int
    title: str
    body: str
    channel: str = "PUSH"


class NotifyResult(BaseModel):
    ok: bool = True
