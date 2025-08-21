from pydantic import BaseModel, Field
from typing import List, Optional
from app.domains.products.store_meta import StoreMeta


class ProductSpecs(BaseModel):
    material: Optional[str] = Field(None, description="소재", example="Oak")
    place_of_use: Optional[str] = Field(
        None, description="사용 장소", example="Living Room"
    )
    width_cm: Optional[float] = Field(None, description="가로(cm)", example=45)
    height_cm: Optional[float] = Field(None, description="세로(cm)", example=50)
    tolerance_cm: Optional[float] = Field(None, description="오차(cm)", example=0.5)
    edition_info: Optional[str] = Field(
        None, description="에디션 정보", example="1st Edition"
    )
    condition_note: Optional[str] = Field(
        None, description="컨디션/주의사항", example="미세 스크래치 존재 가능"
    )


class ProductMeta(BaseModel):
    id: int = Field(..., description="상품 ID")
    name: str = Field(..., description="상품명")
    images: List[str] = Field(..., description="이미지 URL 리스트")
    tags: List[str] = Field(..., description="태그 리스트")
    title: Optional[str] = Field(None, description="타이틀")
    description: Optional[str] = Field(None, description="설명")
    category: Optional[str] = Field(None, description="카테고리")
    store: StoreMeta = Field(..., description="스토어 메타")
    specs: ProductSpecs = Field(..., description="스펙 정보")
