from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional

from app.domains.products.product_meta import ProductSpecs


class ProductAdminListItem(BaseModel):
    id: int
    name: str
    representative_image: Optional[str]
    category: str
    created_at: str
    updated_at: str
    auction_id: Optional[int]
    is_active: bool = Field(
        True, description="상품이 활성화 상태인지 여부", example=True
    )
    is_sold: bool = Field(
        False, description="상품이 판매 완료 상태인지 여부", example=False
    )


class ProductBase(BaseModel):
    id: str
    name: str = Field(..., description="상품 이름", example="Oak Side Table")
    summary: Optional[str] = Field(
        None, description="상품 요약", example="오크 사이드 테이블"
    )
    description: Optional[str] = Field(
        None, description="상품 상세 설명", example="천연 오크로 만든 사이드 테이블"
    )
    price: Decimal = Field(..., description="상품 가격", example="120000.00")
    stock: int = Field(..., description="재고 수량", example=10)
    images: List[str] = Field(
        ...,
        description="이미지 URL 리스트",
        example=[
            "https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png",
            "https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png",
            "https://nafalmvp-products.s3.ap-northeast-2.amazonaws.com/main/product-1-main.png",
        ],
    )
    category: str = Field(..., description="상품 카테고리", example="가구/리빙")
    tags: List[str] = Field(..., description="상품 태그 리스트", example=["가구"])
    specs: ProductSpecs = Field(..., description="상품 스펙 정보")
    store_id: int = Field(..., description="스토어 ID", example=2001)
    shipping_base_fee: int = Field(..., description="기본 배송 요금", example=2500)
    shipping_free_threshold: Optional[int] = Field(
        None, description="배송 무료 기준 금액", example=30000
    )
    shipping_extra_note: Optional[str] = Field(
        None, description="배송 추가 안내", example=None
    )
    courier_name: Optional[str] = Field(
        None, description="배송사 이름", example="CJ대한통운"
    )


class ProductAdminMeta(ProductBase):
    id: int = Field(..., description="상품 ID", example=3001)
    created_at: str = Field(
        ..., description="상품 생성 일시", example="2023-10-01T12:00:00Z"
    )
    updated_at: str = Field(
        ..., description="상품 수정 일시", example="2023-10-01T12:00:00Z"
    )
    auction_id: Optional[int] = Field(
        None, description="경매 ID (경매 상품인 경우)", example=4001
    )
    store_description: Optional[str]
    store_sales_description: Optional[str]
    auction_start_price: Optional[Decimal] = Field(
        None, description="경매 시작 가격", example="50000.00"
    )
    auction_buy_now_price: Optional[Decimal] = Field(
        None, description="경매 즉시 구매 가격", example="200000.00"
    )
    is_active: bool = Field(
        True, description="상품이 활성화 상태인지 여부", example=True
    )
    is_sold: bool = Field(
        False, description="상품이 판매 완료 상태인지 여부", example=False
    )


class ProductCreateOrUpdate(ProductBase):
    id: Optional[int] = Field(
        None, description="상품 ID (업데이트 시 필요)", example=3001
    )
