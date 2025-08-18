from pydantic import BaseModel, Field


class BusinessErrorResponse(BaseModel):
    code: str = Field(..., description="비즈니스 에러 코드")
    message: str = Field(..., description="에러 메시지")


class ServerErrorResponse(BaseModel):
    code: str = Field(..., description="서버 에러 코드, 고정값 INTERNAL_SERVER_ERROR")
    message: str = Field(..., description="에러 메시지")
