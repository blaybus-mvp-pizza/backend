from pydantic import BaseModel, Field
from typing import Optional
from app.domains.common.base_model import BaseResponseModel, BaseRequestModel


class AdminAuctionListItem(BaseModel):
    auction_id: int = Field(..., description="경매 ID")
    product_id: int = Field(..., description="상품 ID")
    product_name: str = Field(..., description="상품명")
    start_price: float = Field(..., description="시작가")
    buy_now_price: Optional[float] = Field(None, description="즉시구매가")
    starts_at: str = Field(..., description="시작일시(KST ISO8601)")
    ends_at: str = Field(..., description="종료일시(KST ISO8601)")
    status: str = Field(..., description="경매 상태 SCHEDULED|RUNNING|ENDED|CANCELLED")
    payment_status: str = Field(..., description="결제 상태(대기/확인/취소)")
    shipment_status: str = Field(..., description="배송 상태(대기/처리/조회/완료)")
    is_won: bool = Field(..., description="낙찰 여부")


class AdminAuctionDetail(BaseModel):
    auction_id: int
    product_id: int
    product_name: str
    store_name: Optional[str] = None
    representative_image: Optional[str] = None

    start_price: float
    min_bid_price: float
    buy_now_price: Optional[float] = None
    deposit_amount: float
    starts_at: str
    ends_at: str
    status: str

    current_highest_bid: Optional[float] = None
    bidder_count: int
    payment_status: str
    shipment_status: str
    is_won: bool


class AdminAuctionUpsertRequest(BaseModel):
    id: Optional[int] = Field(None, description="수정 시 경매 ID")
    product_id: int = Field(..., description="상품 ID")
    start_price: float
    min_bid_price: float
    buy_now_price: Optional[float] = None
    deposit_amount: float
    starts_at: str = Field(..., description="한국시간(KST) ISO8601 입력")
    ends_at: str = Field(..., description="한국시간(KST) ISO8601 입력")
    status: Optional[str] = Field("SCHEDULED", description="기본 SCHEDULED")


class AdminAuctionStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="변경할 상태(CANCELLED|RUNNING|PAUSED)")

class AdminAuctionShipmentInfo(BaseModel):
    shipment_status: str
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None


