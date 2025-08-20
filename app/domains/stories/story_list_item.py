from pydantic import BaseModel, Field

from app.domains.stories.product_brief import ProductBrief


class StoryListItem(BaseModel):
    story_id: int = Field(..., description="스토리 ID")
    product: ProductBrief = Field(..., description="연관 상품 제목/설명/썸네일 url")
    title: str = Field(..., description="스토리 제목")
    content: str = Field(..., description="스토리 내용")
    representative_image: str = Field(..., description="스토리 대표 이미지 URL")
