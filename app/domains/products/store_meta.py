from pydantic import BaseModel
from typing import Optional


class StoreMeta(BaseModel):
    store_id: int
    image_url: Optional[str]
    name: str
    description: Optional[str]
    sales_description: Optional[str]
