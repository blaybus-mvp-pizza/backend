from __future__ import annotations

from typing import Literal, Optional, Set

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.errors import BusinessError
from app.services.s3_storage import S3StorageManager


Entity = Literal["product", "store", "story", "profile"]


AWS_REGION = "ap-northeast-2"
BUCKET_MAP = {
    "product": "nafalmvp-products",
    "store": "nafalmvp-popup-stores",
    "story": "nafalmvp-stories",
    "profile": "nafalmvp-users",
}
CDN_DOMAIN: Optional[str] = None

MAX_UPLOAD_SIZE_MB = 5
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}


def get_s3_manager() -> S3StorageManager:
    return S3StorageManager(region=AWS_REGION, bucket_map=BUCKET_MAP, cdn_domain=CDN_DOMAIN)


class PresignRequest(BaseModel):
    entity: Entity
    filename: str
    contentType: str = Field(alias="contentType")


class PresignResponse(BaseModel):
    uploadUrl: str
    fileUrl: str
    key: str


class UploadResponse(BaseModel):
    fileUrl: str
    key: str


api = APIRouter()


@api.post("/presign", response_model=PresignResponse)
def create_presigned_url(payload: PresignRequest, s3: S3StorageManager = Depends(get_s3_manager)):
    if payload.contentType not in ALLOWED_IMAGE_MIME:
        raise BusinessError("UNSUPPORTED_MIME", "허용되지 않은 MIME 타입")

    try:
        key = s3.generate_key(payload.entity, original_filename=payload.filename)
        bucket = s3.get_bucket(payload.entity)
        # 일부 버킷은 ACL 비활성(Object Ownership enforced)일 수 있으므로 ACL을 생략
        upload_url = s3.create_presigned_put_url(bucket, key, content_type=payload.contentType, acl=None)
        file_url = s3.get_public_url(bucket, key)
        return PresignResponse(uploadUrl=upload_url, fileUrl=file_url, key=key)
    except ValueError as e:
        raise BusinessError("VALIDATION_ERROR", str(e))
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"code": "S3_PRESIGN_FAILED", "message": str(e)})


@api.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    entity: Entity = Form(...),
    s3: S3StorageManager = Depends(get_s3_manager),
):

    try:
        s3.validate_file(file, max_mb=MAX_UPLOAD_SIZE_MB, allowed_mime=ALLOWED_IMAGE_MIME)
    except ValueError as e:
        code = str(e)
        if code in {"FILE_TOO_LARGE", "UNSUPPORTED_MIME"}:
            raise BusinessError(code, "파일 검증 실패")
        raise BusinessError("VALIDATION_ERROR", str(e))

    try:
        key = s3.generate_key(entity, original_filename=file.filename)
        bucket = s3.get_bucket(entity)
        await file.seek(0)
        fileobj = await file.read()
        # ACL 비활성 버킷 호환
        s3.upload_fileobj(fileobj, bucket, key, content_type=file.content_type, acl=None)
        file_url = s3.get_public_url(bucket, key)
        return UploadResponse(fileUrl=file_url, key=key)
    except ValueError as e:
        raise BusinessError("VALIDATION_ERROR", str(e))
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"code": "S3_UPLOAD_FAILED", "message": str(e)})


