from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.domains.common.base_model import BaseResponseModel


class MyAuctionItemStatus(str, Enum):
    RUNNING = "경매 진행중"
    WON_CONFIRMED = "낙찰 확정"
    AUCTION_ENDED = "경매 종료"
    PAUSED = "경매 일시중지"
    SHIPPING = "배송중"
    DELIVERED = "배송완료"


class UserAuctionDashboard(BaseModel):
    running_bid_count: int = Field(..., description="경매 진행 상품: 내가 입찰한 상품 개수")
    pre_shipment_count: int = Field(
        ..., description="입금 확인 중: 내가 낙찰되었고 배송 전 상태"
    )
    shipping_count: int = Field(..., description="배송 중: 내가 낙찰되었고 배송 진행 중")
    delivered_count: int = Field(..., description="배송 완료: 내가 낙찰되었고 배송 완료")


class UserRelatedAuctionItem(BaseResponseModel):
    product_id: int = Field(..., description="상품 ID")
    auction_id: int = Field(..., description="경매 ID")
    image_url: Optional[str] = Field(None, description="상품 대표 이미지 URL")
    product_name: str = Field(..., description="상품명")
    current_highest_bid: Optional[float] = Field(
        None, description="현재 입찰 최고 금액"
    )
    my_bid_amount: Optional[float] = Field(None, description="내가 입찰한 금액(최고)\n")
    status: MyAuctionItemStatus = Field(..., description="항목 상태")
    my_last_bid_at: datetime = Field(..., description="내 마지막 입찰 일시(KST)")


