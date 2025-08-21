from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.domains.common.paging import Page

from app.core.deps import get_db
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts
from app.domains.products.store_meta import StoreMeta
from app.domains.products.service import ProductService
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.products.enums import SortOption, StatusFilter, BiddersFilter, PriceBucket, ProductCategory


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


class ProductsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/ending-soon",
            response_model=Page[ProductListItem],
            summary="마감임박 상품 조회",
            description="경매 종료 임박 순으로 상품을 페이징 조회합니다 (경매 상태 RUNNING).",
            response_description="상품 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {
                    "model": ServerErrorResponse,
                    "description": "서버 내부 오류",
                    "content": {
                        "application/json": {
                            "examples": {
                                "INTERNAL_SERVER_ERROR": {
                                    "value": {
                                        "code": "INTERNAL_SERVER_ERROR",
                                        "message": "서버 내부 오류",
                                    }
                                }
                            }
                        }
                    },
                },
            },
        )
        async def get_ending_soon_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"),
            sort: SortOption = Query(SortOption.ending, description="정렬 recommended|popular|latest|ending"),
            status: StatusFilter = Query(StatusFilter.RUNNING, description="상태 ALL|RUNNING|ENDED"),
            bidders: BiddersFilter = Query(BiddersFilter.ALL, description="입찰자수 ALL|LE_10|BT_10_20|GE_20"),
            price_bucket: PriceBucket = Query(PriceBucket.ALL, description="가격 ALL|LT_10000|BT_10000_30000|BT_30000_50000|BT_50000_150000|BT_150000_300000|BT_300000_500000|CUSTOM"),
            price_min: Optional[float] = Query(None, description="CUSTOM 최소 가격"),
            price_max: Optional[float] = Query(None, description="CUSTOM 최대 가격"),
            category: ProductCategory = Query(ProductCategory.ALL, description="카테고리 코드(ALL 포함)"),
            q: Optional[str] = Query(None, description="키워드 포함 검색"),
        ):
            return service.ending_soon(
                page=page,
                size=size,
                sort=sort,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                category=category.value if isinstance(category, ProductCategory) else category,
                q=q,
            )

        @self.router.get(
            "/recommended",
            response_model=Page[ProductListItem],
            summary="MD 추천 상품 조회",
            description="내부 추천 기준에 따라 상품을 페이징 조회합니다.",
            response_description="상품 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_recommended_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"),
            sort: SortOption = Query(SortOption.recommended, description="정렬 recommended|popular|latest|ending"),
            status: StatusFilter = Query(StatusFilter.RUNNING, description="상태 ALL|RUNNING|ENDED"),
            bidders: BiddersFilter = Query(BiddersFilter.ALL, description="입찰자수 ALL|LE_10|BT_10_20|GE_20"),
            price_bucket: PriceBucket = Query(PriceBucket.ALL, description="가격 ALL|LT_10000|BT_10000_30000|BT_30000_50000|BT_50000_150000|BT_150000_300000|BT_300000_500000|CUSTOM"),
            price_min: Optional[float] = Query(None, description="CUSTOM 최소 가격"),
            price_max: Optional[float] = Query(None, description="CUSTOM 최대 가격"),
            q: Optional[str] = Query(None, description="키워드 포함 검색"),
            category: ProductCategory = Query(ProductCategory.ALL, description="카테고리 코드(ALL 포함)"),
        ):
            return service.recommended(
                page=page,
                size=size,
                sort=sort,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                category=category.value if isinstance(category, ProductCategory) else category,
                q=q,
            )

        @self.router.get(
            "/new",
            response_model=Page[ProductListItem],
            summary="신규 상품 조회",
            description="최근 등록된 상품을 페이징 조회합니다.",
            response_description="상품 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_new_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"),
            sort: SortOption = Query(SortOption.latest, description="정렬 recommended|popular|latest|ending"),
            status: StatusFilter = Query(StatusFilter.RUNNING, description="상태 ALL|RUNNING|ENDED"),
            bidders: BiddersFilter = Query(BiddersFilter.ALL, description="입찰자수 ALL|LE_10|BT_10_20|GE_20"),
            price_bucket: PriceBucket = Query(PriceBucket.ALL, description="가격 ALL|LT_10000|BT_10000_30000|BT_30000_50000|BT_50000_150000|BT_150000_300000|BT_300000_500000|CUSTOM"),
            price_min: Optional[float] = Query(None, description="CUSTOM 최소 가격"),
            price_max: Optional[float] = Query(None, description="CUSTOM 최대 가격"),
            category: ProductCategory = Query(ProductCategory.ALL, description="카테고리 코드(ALL 포함)"),
            q: Optional[str] = Query(None, description="키워드 포함 검색"),
        ):
            return service.newest(
                page=page,
                size=size,
                sort=sort,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                category=category.value if isinstance(category, ProductCategory) else category,
                q=q,
            )

        @self.router.get(
            "/stores/recent",
            response_model=Page[StoreWithProducts],
            summary="최근 오픈 스토어 + 최신 상품 묶음",
            description="최근 오픈한 스토어들을 페이징으로 조회하고, 각 스토어의 최신 상품 일부를 함께 반환합니다.",
            response_description="스토어 + 상품 묶음 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_recent_stores_with_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="스토어 페이지 번호(1부터)"),
            stores: int = Query(10, ge=1, le=50, description="한 페이지에 조회할 스토어 수(최대 50)"),
            size: int = Query(4, ge=1, le=100, description="각 스토어별 포함할 최신 상품 수"),
            sort: SortOption = Query(SortOption.latest, description="정렬 recommended|popular|latest|ending"),
            status: StatusFilter = Query(StatusFilter.RUNNING, description="상태 ALL|RUNNING|ENDED"),
            bidders: BiddersFilter = Query(BiddersFilter.ALL, description="입찰자수 ALL|LE_10|BT_10_20|GE_20"),
            price_bucket: PriceBucket = Query(PriceBucket.ALL, description="가격 ALL|LT_10000|BT_10000_30000|BT_30000_50000|BT_50000_150000|BT_150000_300000|BT_300000_500000|CUSTOM"),
            price_min: Optional[float] = Query(None, description="CUSTOM 최소 가격"),
            price_max: Optional[float] = Query(None, description="CUSTOM 최대 가격"),
            category: ProductCategory = Query(ProductCategory.ALL, description="카테고리 코드(ALL 포함)"),
        ):
            return service.stores_recent(
                page=page,
                stores=stores,
                size=size,
                sort=sort,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                category=category.value if isinstance(category, ProductCategory) else category,
            )

        @self.router.get(
            "/stores",
            response_model=Page[StoreMeta],
            summary="스토어 목록",
            description="스토어의 요약 메타데이터를 페이징 조회합니다.",
            response_description="스토어 메타 리스트",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_store_list(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(20, ge=1, le=100, description="페이지 크기(기본 20, 최대 100)"),
        ):
            return service.store_list(page=page, size=size)

        @self.router.get(
            "/upcoming",
            response_model=Page[ProductListItem],
            summary="오픈예정 상품 조회",
            description="시작 예정인 경매 상품을 페이징 조회합니다 (경매 상태 SCHEDULED).",
            response_description="상품 리스트",
            responses={
                400: {"model": BusinessErrorResponse, "description": "비즈니스 에러"},
                500: {"model": ServerErrorResponse, "description": "서버 내부 오류"},
            },
        )
        async def get_upcoming_products(
            service: ProductService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"),
            sort: SortOption = Query(SortOption.ending, description="정렬 recommended|popular|latest|ending"),
            status: StatusFilter = Query(StatusFilter.SCHEDULED, description="상태 SCHEDULED 고정 또는 ALL"),
            bidders: BiddersFilter = Query(BiddersFilter.ALL, description="입찰자수 ALL|LE_10|BT_10_20|GE_20"),
            price_bucket: PriceBucket = Query(PriceBucket.ALL, description="가격 ALL|LT_10000|BT_10000_30000|BT_30000_50000|BT_50000_150000|BT_150000_300000|BT_300000_500000|CUSTOM"),
            price_min: Optional[float] = Query(None, description="CUSTOM 최소 가격"),
            price_max: Optional[float] = Query(None, description="CUSTOM 최대 가격"),
            category: ProductCategory = Query(ProductCategory.ALL, description="카테고리 코드(ALL 포함)"),
            q: Optional[str] = Query(None, description="키워드 포함 검색"),
        ):
            return service.upcoming(
                page=page,
                size=size,
                sort=sort,
                status=status,
                bidders=bidders,
                price_bucket=price_bucket,
                price_min=price_min,
                price_max=price_max,
                category=category.value if isinstance(category, ProductCategory) else category,
                q=q,
            )


api = ProductsAPI().router
