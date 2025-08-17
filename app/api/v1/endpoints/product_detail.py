from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_meta import StoreMeta
from app.domains.auctions.auction_info import AuctionInfo
from app.domains.auctions.bid_item import BidItem
from app.domains.products.product_meta import ProductMeta
from app.domains.products.service import ProductService


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


class CatalogAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get("/stores/{store_id}/meta", response_model=StoreMeta)
        async def get_store_meta(
            store_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.store_meta(store_id=store_id)

        @self.router.get(
            "/stores/{store_id}/products", response_model=List[ProductListItem]
        )
        async def list_products_by_store(
            store_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(30, ge=1, le=100),
            sort: str = Query(
                "latest", description="recommended|popular|latest|ending"
            ),
        ):
            return service.products_by_store(
                store_id=store_id, sort=sort, page=page, size=size
            )

        @self.router.get("/products/{product_id}/meta", response_model=ProductMeta)
        async def product_meta(
            product_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.product_meta(product_id=product_id)

        @self.router.get("/products/{product_id}/auction", response_model=AuctionInfo)
        async def product_auction_info(
            product_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.product_auction_info(product_id=product_id)

        @self.router.get("/products/{product_id}/bids", response_model=List[BidItem])
        async def product_bids(
            product_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(3, ge=1, le=100),
        ):
            return service.product_bids(product_id=product_id, page=page, size=size)

        @self.router.get(
            "/products/{product_id}/similar", response_model=List[ProductListItem]
        )
        async def product_similar(
            product_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1),
            size: int = Query(4, ge=1, le=100),
        ):
            return service.product_similar(product_id=product_id, page=page, size=size)


api = CatalogAPI().router
