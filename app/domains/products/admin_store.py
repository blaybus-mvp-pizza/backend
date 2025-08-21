from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.stores.popup_store import PopupStore


class StoreAdminMeta(BaseModel):
    id: int = Field(..., description="스토어 ID")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    name: str = Field(..., description="스토어명")
    description: Optional[str] = Field(None, description="소개")
    sales_description: Optional[str] = Field(None, description="판매 관련 설명")
    starts_at: Optional[str] = Field(None, description="팝업 시작일시 (ISO 8601 형식)")
    ends_at: Optional[str] = Field(None, description="팝업 종료일시 (ISO 8601 형식)")

    model_config = {
        "from_attributes": True,
    }

    @classmethod
    def from_orm(cls, obj: PopupStore) -> "StoreAdminMeta":
        return cls(
            id=obj.id,
            image_url=obj.image_url,
            name=obj.name,
            description=obj.description,
            sales_description=obj.sales_description,
            starts_at=obj.starts_at.isoformat() if obj.starts_at else None,
            ends_at=obj.ends_at.isoformat() if obj.ends_at else None,
        )


class StoreCreateOrUpdate(BaseModel):
    id: Optional[int] = Field(None, description="스토어 ID (업데이트 시 필요)")
    name: str = Field(None, description="스토어명")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    description: Optional[str] = Field(None, description="소개")
    sales_description: Optional[str] = Field(None, description="판매 관련 설명")
    starts_at: Optional[str] = Field(None, description="팝업 시작일시 (ISO 8601 형식)")
    ends_at: Optional[str] = Field(None, description="팝업 종료일시 (ISO 8601 형식)")
