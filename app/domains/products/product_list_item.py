from pydantic import BaseModel, Field
from typing import Optional


class ProductListItem(BaseModel):
    product_id: int = Field(..., description="상품 ID")
    popup_store_name: str = Field(..., description="팝업 스토어 이름")
    product_name: str = Field(..., description="상품명")
    current_highest_bid: Optional[float] = Field(None, description="현재 최고 입찰가")
    buy_now_price: Optional[float] = Field(None, description="즉시구매가")
    representative_image: Optional[str] = Field(None, description="대표 이미지 URL")
    auction_ends_at: Optional[str] = Field(None, description="경매 종료 일시(ISO8601)")
