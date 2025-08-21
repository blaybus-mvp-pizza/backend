from datetime import datetime
from tkinter import image_types
from turtle import st
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, and_
from app.schemas.products import Product, ProductImage
from app.schemas.products.product_tag import ProductTag
from app.schemas.products.tag import Tag
from app.schemas.stores import PopupStore
from app.schemas.auctions import Auction, Bid
from app.domains.products.mappers import rows_to_product_items
from app.domains.products.store_meta import StoreMeta
from app.domains.products.product_meta import ProductMeta, ProductSpecs
from app.domains.products.product_list_item import ProductListItem
from app.domains.products.store_with_products import StoreWithProducts


class ProductAdminWriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_store(
        self,
        *,
        name: str,
        image_url: Optional[str],
        description: Optional[str],
        sales_description: Optional[str],
        starts_at: datetime,
        ends_at: datetime,
    ) -> PopupStore:
        store = PopupStore(
            name=name,
            image_url=image_url,
            description=description,
            sales_description=sales_description,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        self.db.add(store)
        self.db.flush()
        return store

    def update_store(
        self,
        *,
        store: PopupStore,
        name: str,
        image_url: Optional[str],
        description: Optional[str],
        sales_description: Optional[str],
        starts_at: datetime,
        ends_at: datetime,
    ) -> PopupStore:
        store.name = name
        store.image_url = image_url
        store.description = description
        store.sales_description = sales_description
        store.starts_at = starts_at
        store.ends_at = ends_at
        self.db.flush()
        self.db.refresh(store)
        return store

    def create_product(
        self,
        *,
        name: str,
        summary: Optional[str],
        description: Optional[str],
        price: float,
        stock: int,
        images: List[str],
        category: str,
        tags: List[str],
        specs: ProductSpecs,
        store_id: int,
        shipping_base_fee: int,
        shipping_free_threshold: Optional[int],
        shipping_extra_note: Optional[str],
        courier_name: Optional[str],
    ) -> Product:
        product = Product(
            name=name,
            summary=summary,
            description=description,
            price=price,
            stock=stock,
            category=category,
            popup_store_id=store_id,
            shipping_base_fee=shipping_base_fee,
            shipping_free_threshold=shipping_free_threshold,
            shipping_extra_note=shipping_extra_note,
            courier_name=courier_name,
            material=specs.material,
            place_of_use=specs.place_of_use,
            width_cm=specs.width_cm,
            height_cm=specs.height_cm,
            tolerance_cm=specs.tolerance_cm,
            edition_info=specs.edition_info,
            condition_note=specs.condition_note,
        )

        for idx, image_url in enumerate(images):
            product.images.append(
                ProductImage(
                    image_type="MAIN" if idx == 0 else "DETAIL",
                    image_url=image_url,
                    sort_order=idx,
                )
            )

        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)

        # 태그 생성
        for tag in tags:
            existing_tag = self.db.execute(
                select(Tag).where(Tag.name == tag)
            ).scalar_one_or_none()
            if not existing_tag:
                existing_tag = Tag(name=tag)
                self.db.add(existing_tag)
                self.db.flush()
                self.db.refresh(existing_tag)

            product_tag = ProductTag(product_id=product.id, tag_id=existing_tag.id)
            self.db.add(product_tag)
        self.db.flush()

        return product

    def update_product(
        self,
        *,
        product: Product,
        name: str,
        summary: Optional[str],
        description: Optional[str],
        price: float,
        stock: int,
        images: List[str],
        category: str,
        tags: List[str],
        specs: ProductSpecs,
        store_id: int,
        shipping_base_fee: int,
        shipping_free_threshold: Optional[int],
        shipping_extra_note: Optional[str],
        courier_name: Optional[str],
    ) -> Product:
        product.name = name
        product.summary = summary
        product.description = description
        product.price = price
        product.stock = stock
        product.category = category
        product.popup_store_id = store_id
        product.shipping_base_fee = shipping_base_fee
        product.shipping_free_threshold = shipping_free_threshold
        product.shipping_extra_note = shipping_extra_note
        product.courier_name = courier_name
        product.material = specs.material
        product.place_of_use = specs.place_of_use
        product.width_cm = specs.width_cm
        product.height_cm = specs.height_cm
        product.tolerance_cm = specs.tolerance_cm
        product.edition_info = specs.edition_info
        product.condition_note = specs.condition_note

        # TODO: 이미지와 태그 동기화 로직 수정 필요
        self.db.flush()
        self.db.refresh(product)

        return product
