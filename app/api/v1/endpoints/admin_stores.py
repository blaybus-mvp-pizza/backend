from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional
from app.domains.common.error_response import BusinessErrorResponse, ServerErrorResponse
from app.domains.common.paging import Page

from app.core.deps import get_db
from app.domains.products.admin_service import ProductAdminService
from app.domains.products.admin_store import StoreCreateOrUpdate, StoreAdminMeta
from app.domains.products.store_meta import StoreMeta


def get_product_service(db: Session = Depends(get_db)) -> ProductAdminService:
    return ProductAdminService(db)


class AdminStoresAPI:
    def __init__(self):
        self.router = APIRouter()

        @self.router.get(
            "/",
            response_model=Page[StoreMeta],
            summary="스토어 목록 페이지 조회",
            description="스토어의 요약 메타데이터를 페이징 조회합니다.",
            response_description="스토어 목록 페이지",
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
        async def get_store_list_page(
            service: ProductAdminService = Depends(get_product_service),
            page: int = Query(1, ge=1, description="페이지 번호(1부터)"),
            size: int = Query(
                20, ge=1, le=100, description="페이지 크기(기본 20, 최대 100)"
            ),
        ) -> Page[StoreMeta]:
            return service.store_list(page=page, size=size)

        @self.router.get(
            "/modal",
            response_model=List[StoreMeta],
            summary="스토어 모달용 리스트 조회",
            description="스토어 목록을 모달용으로 전체 조회합니다. 추후 가능하면 검색 기능을 추가할 수 있습니다.",
            response_description="스토어 모달용 리스트",
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
        async def get_store_modal_list(
            service: ProductAdminService = Depends(get_product_service),
        ) -> List[StoreMeta]:
            return service.store_modal_list()

        @self.router.get(
            "/{store_id}",
            response_model=StoreAdminMeta,
            summary="스토어 상세 조회",
            description="스토어 ID로 스토어 정보를 조회합니다.",
            response_description="스토어 상세 정보",
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
        async def get_store_detail(
            store_id: int,
            service: ProductAdminService = Depends(get_product_service),
        ) -> StoreAdminMeta:
            return service.store_meta_full(store_id=store_id)

        @self.router.post(
            "/",
            response_model=StoreAdminMeta,
            summary="스토어 생성 or 수정",
            description="스토어 정보를 생성하거나 수정합니다. 스토어 ID가 없으면 생성, 있으면 수정합니다.",
            response_description="스토어 생성/수정 결과",
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
        async def create_or_update_store(
            store_data: StoreCreateOrUpdate,
            service: ProductAdminService = Depends(get_product_service),
        ) -> StoreAdminMeta:
            if store_data.id is None:
                return service.create_store(store_data=store_data)
            else:
                return service.update_store(store_data=store_data)


api = AdminStoresAPI().router
