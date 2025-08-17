from pydantic import BaseModel, Field
from typing import Optional


class UserBrief(BaseModel):
    id: int = Field(..., description="사용자 ID")
    name: Optional[str] = Field(None, description="사용자명")
    profile_image: Optional[str] = Field(None, description="프로필 이미지 URL")


class BidItem(BaseModel):
    user: UserBrief = Field(..., description="입찰자 정보")
    bid_amount: float = Field(..., description="입찰 금액")
    bid_at: str = Field(..., description="입찰 시각(ISO8601)")
