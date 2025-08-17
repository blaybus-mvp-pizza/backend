from cmath import phase
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    nickname: str


class UserRead(BaseModel):
    id: int
    email: str
    nickname: str
    phone_number: str | None = None
    profile_image_url: str | None = None
    is_phone_verified: bool = False

    model_config = {
        "from_attributes": True,
    }


class UserUpdate(BaseModel):
    nickname: str
    phone_number: str | None = None
    profile_image_url: str | None = None
    is_phone_verified: bool = False

    model_config = {
        "from_attributes": True,
    }
