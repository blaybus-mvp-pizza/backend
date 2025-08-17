from pydantic import BaseModel
from typing import List, Optional
from app.domains.products.store_meta import StoreMeta


class ProductSpecs(BaseModel):
    material: Optional[str]
    place_of_use: Optional[str]
    width_cm: Optional[float]
    height_cm: Optional[float]
    tolerance_cm: Optional[float]
    edition_info: Optional[str]
    condition_note: Optional[str]


class ProductMeta(BaseModel):
    id: int
    name: str
    images: List[str]
    tags: List[str]
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    store: StoreMeta
    specs: ProductSpecs
