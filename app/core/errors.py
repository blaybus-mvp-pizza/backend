from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status


class BusinessError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message


def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"code": exc.code, "message": exc.message},
    )


def internal_error_handler(request: Request, exc: Exception):
    # NOTE: 운영에서는 로깅/트레이싱 추가 권장
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_SERVER_ERROR", "message": "서버 내부 오류"},
    )
