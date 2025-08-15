from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    username: str

    class Config:
        from_attributes = True
