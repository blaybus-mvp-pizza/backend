from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete, select
from app.schemas.products import Product, ProductImage
from app.schemas.products.product_tag import ProductTag
from app.schemas.products.tag import Tag
from app.schemas.stores import PopupStore
from app.domains.products.product_meta import ProductSpecs


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

    def sync_product_tags(self, *, tags: List[str], product_id: int):
        """
        주어진 tags 리스트를 기준으로 product_id의 태그를 동기화합니다.
        - 새로운 태그는 생성
        - 기존에 있지만 리스트에 없는 태그는 연결 해제
        """
        # 1. 현재 상품에 연결된 태그 가져오기
        current_tags = (
            self.db.execute(
                select(Tag).join(ProductTag).where(ProductTag.product_id == product_id)
            )
            .scalars()
            .all()
        )

        current_tag_names = {tag.name for tag in current_tags}
        new_tag_names = set(tags)

        # 2. 삭제할 태그 결정 (DB에 연결되어 있지만 새 리스트에 없는 태그)
        tags_to_remove = [tag for tag in current_tags if tag.name not in new_tag_names]
        for tag in tags_to_remove:
            self.db.execute(
                delete(ProductTag).where(
                    ProductTag.product_id == product_id, ProductTag.tag_id == tag.id
                )
            )

        # 3. 추가할 태그 결정 (리스트에 있지만 DB에 없는 태그)
        tags_to_add_names = new_tag_names - current_tag_names
        tag_objects_to_add = []

        for tag_name in tags_to_add_names:
            tag_obj = self.db.execute(
                select(Tag).where(Tag.name == tag_name)
            ).scalar_one_or_none()

            # 태그가 DB에 없으면 생성
            if not tag_obj:
                tag_obj = Tag(name=tag_name)
                self.db.add(tag_obj)
                self.db.flush()

            # ProductTag에 연결
            self.db.add(ProductTag(product_id=product_id, tag_id=tag_obj.id))
            tag_objects_to_add.append((tag_obj.id, tag_obj.name))

        # 4. 최종 연결된 태그 반환
        final_tags = self.db.execute(
            select(Tag.id, Tag.name)
            .join(ProductTag)
            .where(ProductTag.product_id == product_id)
        ).all()
        print(final_tags)

    def sync_product_images(self, *, product: Product, new_image_urls: list[str]):
        """
        product.images와 new_image_urls를 동기화
        - 새 URL이 있으면 추가
        - 기존에 없어진 URL은 삭제
        """
        # 현재 이미지 URL 집합
        existing_urls = {img.image_url: img for img in product.images}

        # 새 URL 집합
        new_urls = set(new_image_urls)

        # 삭제할 이미지 찾기
        for url in set(existing_urls) - new_urls:
            self.db.execute(
                delete(ProductImage).where(
                    ProductImage.product_id == product.id, ProductImage.image_url == url
                )
            )

        # 추가할 이미지 찾기
        for idx, url in enumerate(new_image_urls):
            if url not in existing_urls:
                product.images.append(
                    ProductImage(
                        image_type="MAIN" if idx == 0 else "DETAIL",
                        image_url=url,
                        sort_order=idx,
                    )
                )
            else:
                # 기존 이미지라면 sort_order 갱신
                existing_urls[url].sort_order = idx
                existing_urls[url].image_type = "MAIN" if idx == 0 else "DETAIL"

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

        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)

        self.sync_product_images(product=product, new_image_urls=images)
        self.sync_product_tags(tags=tags, product_id=product.id)
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

        self.db.flush()
        self.db.refresh(product)
        self.sync_product_images(product=product, new_image_urls=images)
        self.sync_product_tags(tags=tags, product_id=product.id)
        self.db.flush()

        return product
