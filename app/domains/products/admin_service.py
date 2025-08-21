from ast import Store
from datetime import datetime
from typing import List
from app.domains.products.enums import (
    SortOption,
    StatusFilter,
    BiddersFilter,
    PriceBucket,
    ProductAdminStatusFilter,
)
from app.core.errors import BusinessError

from app.domains.common.paging import Page, paginate
from sqlalchemy.orm import Session

from app.domains.common.str_to_datetime import str_to_datetime
from app.domains.common.tx import transactional
from app.domains.products.admin_store import (
    StoreCreateOrUpdate,
    StoreAdminMeta,
)
from app.repositories.product_admin_read import ProductAdminReadRepository

from app.domains.products.store_meta import StoreMeta

from app.domains.products.mappers import rows_to_product_items
from app.repositories.product_admin_write import ProductAdminWriteRepository
from app.domains.products.admin_product import (
    ProductAdminListItem,
    ProductAdminMeta,
    ProductCreateOrUpdate,
)
from sqlalchemy import select
from app.schemas.products import Product as ProductModel


class ProductAdminService:
    def __init__(self, db: Session):
        self.db = db
        self.products_admin_read = ProductAdminReadRepository(db)
        self.products_admin_write = ProductAdminWriteRepository(db)

    def store_list(self, *, page: int, size: int) -> Page[StoreMeta]:
        """스토어 목록 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.products_admin_read.store_list(limit=size, offset=offset)
        return paginate(items, page, size, total)

    def store_modal_list(self) -> List[StoreMeta]:
        """스토어 모달용 전체 목록 조회"""
        items, _ = self.products_admin_read.store_list()
        return [StoreMeta.model_validate(item) for item in items]

    def store_meta_full(self, *, store_id: int) -> StoreAdminMeta:
        """스토어 메타데이터 상세 조회 (전체 정보 포함)"""
        store = self.products_admin_read.get_store_by_id(store_id)
        if not store:
            raise BusinessError(code=404, message="스토어를 찾을 수 없습니다.")
        return StoreAdminMeta.from_orm(store)

    def create_store(self, *, store_data: StoreCreateOrUpdate) -> StoreAdminMeta:
        """스토어 생성"""
        starts_at = str_to_datetime(store_data.starts_at)
        ends_at = str_to_datetime(store_data.ends_at)
        if starts_at is not None and ends_at is not None and starts_at > ends_at:
            raise BusinessError(
                code=400, message="스토어 시작일시는 종료일시보다 이전이어야 합니다."
            )
        with transactional(self.db):
            store = self.products_admin_write.create_store(
                name=store_data.name,
                image_url=store_data.image_url,
                description=store_data.description,
                sales_description=store_data.sales_description,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            return StoreAdminMeta.from_orm(store)

    def update_store(self, *, store_data: StoreCreateOrUpdate) -> StoreAdminMeta:
        """스토어 정보 수정"""
        store = self.products_admin_read.get_store_by_id(store_data.id)
        if not store:
            raise BusinessError(code=404, message="스토어를 찾을 수 없습니다.")
        starts_at = str_to_datetime(store_data.starts_at)
        ends_at = str_to_datetime(store_data.ends_at)
        if starts_at is not None and ends_at is not None and starts_at > ends_at:
            raise BusinessError(
                code=400, message="스토어 시작일시는 종료일시보다 이전이어야 합니다."
            )
        with transactional(self.db):
            updated_store = self.products_admin_write.update_store(
                store=store,
                name=store_data.name,
                image_url=store_data.image_url,
                description=store_data.description,
                sales_description=store_data.sales_description,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            return StoreAdminMeta.from_orm(updated_store)

    def product_admin_list(
        self,
        *,
        page: int,
        size: int,
        status: ProductAdminStatusFilter = ProductAdminStatusFilter.ALL,
        category: str | None = None,
        q: str | None = None,
    ) -> Page[ProductAdminListItem]:
        """관리자용 상품 목록 조회 (페이지네이션)"""
        offset = (page - 1) * size
        items, total = self.products_admin_read.product_admin_list(
            limit=size,
            offset=offset,
            status=(
                status.value if isinstance(status, ProductAdminStatusFilter) else status
            ),
            category=category,
            q=q,
        )
        return paginate(items, page, size, total)

    def product_admin_meta(self, *, product_id: int) -> ProductAdminMeta:
        """관리자용 상품 상세 메타 조회"""
        return self.products_admin_read.product_admin_meta(product_id)

    def create_product_admin(self, data: ProductCreateOrUpdate) -> ProductAdminMeta:
        """관리자용 상품 생성"""
        store = self.products_admin_read.get_store_by_id(data.store_id)
        if not store:
            raise BusinessError(code=404, message="스토어를 찾을 수 없습니다.")

        with transactional(self.db):
            product = self.products_admin_write.create_product(
                name=data.name,
                summary=data.summary,
                description=data.description,
                price=float(data.price),
                stock=data.stock,
                images=data.images,
                category=data.category,
                tags=data.tags,
                specs=data.specs,
                store_id=data.store_id,
                shipping_base_fee=data.shipping_base_fee,
                shipping_free_threshold=data.shipping_free_threshold,
                shipping_extra_note=data.shipping_extra_note,
                courier_name=data.courier_name,
            )
            return self.products_admin_read.product_admin_meta(product.id)

    def update_product_admin(self, data: ProductCreateOrUpdate) -> ProductAdminMeta:
        """관리자용 상품 수정"""

        store = self.products_admin_read.get_store_by_id(data.store_id)
        if not store:
            raise BusinessError(code=404, message="스토어를 찾을 수 없습니다.")

        product = self.products_admin_read.get_product_by_id(data.id)
        if not product:
            raise BusinessError(code=404, message="상품을 찾을 수 없습니다.")

        with transactional(self.db):
            updated = self.products_admin_write.update_product(
                product=product,
                name=data.name,
                summary=data.summary,
                description=data.description,
                price=float(data.price),
                stock=data.stock,
                images=data.images,
                category=data.category,
                tags=data.tags,
                specs=data.specs,
                store_id=data.store_id,
                shipping_base_fee=data.shipping_base_fee,
                shipping_free_threshold=data.shipping_free_threshold,
                shipping_extra_note=data.shipping_extra_note,
                courier_name=data.courier_name,
            )
            return self.products_admin_read.product_admin_meta(updated.id)
