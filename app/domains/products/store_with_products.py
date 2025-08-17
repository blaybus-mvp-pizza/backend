from pydantic import BaseModel, Field
from typing import List
from app.domains.products.store_meta import StoreMeta
from app.domains.products.product_list_item import ProductListItem


class StoreWithProducts(BaseModel):
    store: StoreMeta = Field(..., description="스토어 메타")
    products: List[ProductListItem] = Field(..., description="해당 스토어의 상품 목록")
