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
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


class CatalogAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/stores/{store_id}/meta",
            response_model=StoreMeta,
            summary="스토어 메타데이터",
            description="스토어의 상세 메타데이터를 조회합니다.",
            response_description="스토어 메타",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_store_meta(
            store_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.store_meta(store_id=store_id)

        @self.router.get(
            "/stores/{store_id}/products",
            response_model=List[ProductListItem],
            summary="스토어 상품 목록",
            description="특정 스토어의 상품을 정렬/페이징하여 조회합니다.",
            response_description="상품 리스트",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def list_products_by_store(
            store_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(
                30, ge=1, le=100, description="페이지 크기(기본 30, 최대 100)"
            ),
            sort: str = Query(
                "latest", description="정렬: recommended|popular|latest|ending"
            ),
        ):
            return service.products_by_store(
                store_id=store_id, sort=sort, page=page, size=size
            )

        @self.router.get(
            "/products/{product_id}/meta",
            response_model=ProductMeta,
            summary="상품 메타데이터",
            description="상품의 상세 메타데이터를 조회합니다.",
            response_description="상품 메타",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def product_meta(
            product_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.product_meta(product_id=product_id)

        @self.router.get(
            "/products/{product_id}/auction",
            response_model=AuctionInfo,
            summary="상품 경매 정보",
            description="상품의 현재 경매 상태/입찰 스텝/보증금 등을 조회합니다.",
            response_description="경매 정보",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def product_auction_info(
            product_id: int, service: ProductService = Depends(get_product_service)
        ):
            return service.product_auction_info(product_id=product_id)

        @self.router.get(
            "/products/{product_id}/bids",
            response_model=List[BidItem],
            summary="상품 입찰 내역",
            description="상품의 입찰 내역을 페이징 조회합니다.",
            response_description="입찰 리스트",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def product_bids(
            product_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(3, ge=1, le=100, description="페이지 크기(기본 3)"),
        ):
            return service.product_bids(product_id=product_id, page=page, size=size)

        @self.router.get(
            "/products/{product_id}/similar",
            response_model=List[ProductListItem],
            summary="유사 상품",
            description="동일 스토어 기준 유사 상품을 조회합니다.",
            response_description="상품 리스트",
        )
        async def product_similar(
            product_id: int,
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(4, ge=1, le=100, description="페이지 크기(기본 4)"),
        ):
            return service.product_similar(product_id=product_id, page=page, size=size)


api = CatalogAPI().router
