from pydantic import BaseModel, Field
from typing import Optional


class StoreMeta(BaseModel):
    store_id: int = Field(..., description="스토어 ID")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    name: str = Field(..., description="스토어명")
    description: Optional[str] = Field(None, description="소개")
    sales_description: Optional[str] = Field(None, description="판매 관련 설명")
