from pydantic import BaseModel, Field
from typing import List, Optional


class AuctionInfo(BaseModel):
    auction_id: int = Field(..., description="경매 ID")
    buy_now_price: Optional[float] = Field(None, description="즉시구매가")
    current_highest_bid: Optional[float] = Field(None, description="현재 최고 입찰가")
    bid_steps: List[float] = Field(..., description="제안되는 입찰 스텝 가격들")
    starts_at: str = Field(..., description="경매 시작 시각(ISO8601)")
    ends_at: str = Field(..., description="경매 종료 시각(ISO8601)")
    start_price: float = Field(..., description="시작가")
    min_bid_price: float = Field(..., description="최소 입찰가")
    deposit_amount: float = Field(..., description="보증금")
    bidder_count: int = Field(..., description="입찰자 수")
