from pydantic import BaseModel
from typing import List
from app.domains.products.store_meta import StoreMeta
from app.domains.products.product_list_item import ProductListItem


class StoreWithProducts(BaseModel):
    store: StoreMeta
    products: List[ProductListItem]
