from pydantic import BaseModel, Field


class ProductBrief(BaseModel):
    id: int = Field(..., description="상품 ID")
    name: str = Field(..., description="상품 이름")
    summary: str = Field(..., description="상품 간단한 설명")
    image: str = Field(..., description="상품 대표 이미지 URL")
