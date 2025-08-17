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
