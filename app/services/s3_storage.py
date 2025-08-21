from __future__ import annotations

from typing import Dict, Literal, Optional, Set, Tuple
import datetime as dt
import mimetypes
import os

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError


Entity = Literal["product", "store", "story", "profile"]


class S3StorageManager:
    def __init__(
        self,
        *,
        region: str,
        bucket_map: Dict[Entity, str],
        cdn_domain: Optional[str] = None,
    ) -> None:
        self.region = region
        self.bucket_map = bucket_map
        self.cdn_domain = cdn_domain.strip() if cdn_domain else None
        # Use default credential chain (ENV, shared config, IAM role)
        self._s3_client = boto3.client("s3", region_name=region, config=BotoConfig(s3={"addressing_style": "virtual"}))

    def get_bucket(self, entity: Entity) -> str:
        if entity not in self.bucket_map:
            raise ValueError(f"Unsupported entity: {entity}")
        return self.bucket_map[entity]

    def _ensure_extension(self, original_filename: str, mime: Optional[str]) -> str:
        name, ext = os.path.splitext(original_filename)
        ext = (ext or "").lower().lstrip(".")
        if ext:
            return ext
        guessed = None
        if mime:
            guessed = mimetypes.guess_extension(mime)
        if guessed:
            return guessed.lstrip(".")
        # default to png if cannot guess
        return "png"

    def generate_key(
        self,
        entity: Entity,
        *,
        original_filename: str,
    ) -> str:
        timestamp = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ext = (os.path.splitext(original_filename)[1] or ".png").lstrip(".")
        ext = ext.lower()

        if entity == "product":
            return f"main/product-{timestamp}.{ext}"
        if entity == "store":
            return f"store-{timestamp}.{ext}"
        if entity == "story":
            return f"story-{timestamp}.{ext}"
        if entity == "profile":
            return f"profile-image/user-{timestamp}.{ext}"
        raise ValueError(f"Unsupported entity: {entity}")

    def get_public_url(self, bucket: str, key: str) -> str:
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        return f"https://{bucket}.s3.{self.region}.amazonaws.com/{key}"

    def validate_file(
        self,
        upload_file,
        *,
        max_mb: int,
        allowed_mime: Set[str],
    ) -> Tuple[str, str]:
        # upload_file is a starlette UploadFile or file-like; must have content_type and file
        content_type = getattr(upload_file, "content_type", None) or getattr(upload_file, "headers", {}).get("content-type")
        if not content_type:
            # final fallback by filename
            content_type = mimetypes.guess_type(getattr(upload_file, "filename", ""))[0]
        if not content_type or content_type not in allowed_mime:
            raise ValueError("UNSUPPORTED_MIME")

        # size check: try to get size from file-like object
        fileobj = getattr(upload_file, "file", None) or upload_file
        current_pos = None
        try:
            current_pos = fileobj.tell()
        except Exception:
            current_pos = None
        try:
            if current_pos is not None:
                fileobj.seek(0, os.SEEK_END)
                size_bytes = fileobj.tell()
                fileobj.seek(current_pos, os.SEEK_SET)
            else:
                # read to measure; then reset if possible
                data = fileobj.read()
                size_bytes = len(data)
                try:
                    fileobj.seek(0)
                except Exception:
                    pass
        except Exception:
            size_bytes = None

        if size_bytes is not None:
            if size_bytes > max_mb * 1024 * 1024:
                raise ValueError("FILE_TOO_LARGE")

        ext = self._ensure_extension(getattr(upload_file, "filename", ""), content_type)
        return ext, content_type

    def create_presigned_put_url(
        self,
        bucket: str,
        key: str,
        *,
        content_type: str,
        expires_in: int = 300,
        acl: Optional[str] = "public-read",
    ) -> str:
        try:
            params = {
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            }
            if acl:
                params["ACL"] = acl
            url = self._s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            return url
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"S3_PRESIGN_FAILED: {e}")

    def upload_fileobj(
        self,
        fileobj,
        bucket: str,
        key: str,
        *,
        content_type: str,
        acl: Optional[str] = "public-read",
    ) -> None:
        try:
            # reset to start if possible
            try:
                fileobj.seek(0)
            except Exception:
                pass
            kwargs = {
                "Bucket": bucket,
                "Key": key,
                "Body": fileobj,
                "ContentType": content_type,
            }
            if acl:
                kwargs["ACL"] = acl
            self._s3_client.put_object(**kwargs)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"S3_UPLOAD_FAILED: {e}")


