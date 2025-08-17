from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    page: int
    size: int
    total: int


def paginate(items: List[T], page: int, size: int, total: int) -> Page[T]:
    return Page(items=items, page=page, size=size, total=total)
