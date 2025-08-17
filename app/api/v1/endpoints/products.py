from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts
from app.domains.products.store_meta import StoreMeta
from app.domains.products.service import ProductService
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


class ProductsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/ending-soon",
            response_model=List[ProductListItem],
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
            size: int = Query(
                4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"
            ),
        ):
            return service.ending_soon(page=page, size=size)

        @self.router.get(
            "/recommended",
            response_model=List[ProductListItem],
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
            size: int = Query(
                4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"
            ),
        ):
            return service.recommended(page=page, size=size)

        @self.router.get(
            "/new",
            response_model=List[ProductListItem],
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
            size: int = Query(
                4, ge=1, le=100, description="페이지 크기(기본 4, 최대 100)"
            ),
        ):
            return service.newest(page=page, size=size)

        @self.router.get(
            "/stores/recent",
            response_model=List[StoreWithProducts],
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
            stores: int = Query(
                10, ge=1, le=50, description="한 페이지에 조회할 스토어 수(최대 50)"
            ),
            size: int = Query(
                4, ge=1, le=100, description="각 스토어별 포함할 최신 상품 수"
            ),
        ):
            return service.stores_recent(page=page, stores=stores, size=size)

        @self.router.get(
            "/stores",
            response_model=List[StoreMeta],
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
            size: int = Query(
                20, ge=1, le=100, description="페이지 크기(기본 20, 최대 100)"
            ),
        ):
            return service.store_list(page=page, size=size)


api = ProductsAPI().router
