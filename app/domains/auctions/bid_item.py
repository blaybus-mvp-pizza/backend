from pydantic import BaseModel
from typing import Optional


class UserBrief(BaseModel):
    id: int
    name: Optional[str] = None
    profile_image: Optional[str] = None


class BidItem(BaseModel):
    user: UserBrief
    bid_amount: float
    bid_at: str
