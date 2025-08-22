from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.common.paging import Page

from app.core.deps import get_db
from app.domains.products.admin_service import ProductAdminService
from app.domains.products.enums import ProductCategory
from app.domains.products.admin_product import (
    ProductAdminListItem,
    ProductAdminMeta,
    ProductCreateOrUpdate,
)


def get_product_service(db: Session = Depends(get_db)) -> ProductAdminService:
    return ProductAdminService(db)


class AdminProductsAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "",
            response_model=Page[ProductAdminListItem],
            summary="상품 목록 페이지 조회",
            description="상품의 요약 메타데이터를 페이징 조회합니다.",
            response_description="상품 목록 페이지",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {
                    "model": ServerErrorResponse,
                    "description": "서버 내부 오류",
                },
            },
        )
        async def get_product_list_page(
            service: ProductAdminService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(
                20, ge=1, le=100, description="페이지 크기(기본 20, 최대 100)"
            ),
            is_active: Optional[bool] = Query(
                None,
                description="상품 활성화 상태 필터 None (전체), True (활성화), False (비활성화)",
            ),
            is_sold: Optional[bool] = Query(
                None,
                description="상품 판매 완료 상태 필터 None (전체), True (판매 완료), False (판매 중)",
            ),
            store_id: Optional[int] = Query(
                None, description="스토어 ID 필터. None이면 전체 조회"
            ),
            category: ProductCategory = Query(
                ProductCategory.ALL,
                description="카테고리 ALL|가구/리빙|키친/테이블웨어|디지털/가전|패션/잡화|아트/컬렉터블|조명/소품|오피스/비즈니스",
            ),
            q: Optional[str] = Query(
                None, description="검색어 (상품명, 상품 summary, 상품 description)"
            ),
        ) -> Page[ProductAdminListItem]:
            return service.product_admin_list(
                page=page,
                size=size,
                is_active=is_active,
                is_sold=is_sold,
                store_id=store_id,
                category=category,
                q=q,
            )

        @self.router.get(
            "/{product_id}",
            response_model=ProductAdminMeta,
            summary="상품 상세 조회",
            description="상품의 상세 메타데이터를 조회합니다.",
            response_description="상품 상세 정보",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                404: {
                    "model": BusinessErrorResponse,
                    "description": "상품을 찾을 수 없음",
                },
                500: {
                    "model": ServerErrorResponse,
                    "description": "서버 내부 오류",
                },
            },
        )
        async def get_product_detail(
            product_id: int,
            service: ProductAdminService = Depends(get_product_service),
        ) -> ProductAdminMeta:
            return service.product_admin_meta(product_id=product_id)

        @self.router.post(
            "",
            response_model=ProductAdminMeta,
            summary="상품 생성 or 수정",
            description="상품을 생성하거나 수정합니다. 상품 ID가 없으면 생성, 있으면 수정합니다.",
            response_description="생성된 상품의 상세 정보",
            responses={
                400: {
                    "model": BusinessErrorResponse,
                    "description": "비즈니스 에러",
                },
                500: {
                    "model": ServerErrorResponse,
                    "description": "서버 내부 오류",
                },
            },
        )
        async def create_product(
            product_data: ProductCreateOrUpdate,
            service: ProductAdminService = Depends(get_product_service),
        ) -> ProductAdminMeta:
            print(product_data.id)
            if product_data.id is None:
                return service.create_product_admin(product_data)
            else:
                return service.update_product_admin(product_data)


api = AdminProductsAPI().router
