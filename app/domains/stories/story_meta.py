from pydantic import BaseModel, Field
from typing import List, Optional

from app.domains.stories.product_brief import ProductBrief


class StoryMeta(BaseModel):
    story_id: int = Field(..., description="스토리 ID")
    product: ProductBrief = Field(..., description="연관 상품 제목/설명/썸네일 url")
    title: str = Field(..., description="스토리 제목")
    content: str = Field(..., description="스토리 내용")
    created_at: str = Field(..., description="스토리 생성 일시(ISO8601)")
    images: List[str] = Field(..., description="스토리 이미지 URL 리스트")
