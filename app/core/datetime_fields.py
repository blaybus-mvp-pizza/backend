"""
Pydantic 모델에서 자동 시간대 변환을 위한 커스텀 필드
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import field_validator, Field
from pydantic._internal._validators import CoreValidator
from .timezone import utc_to_kst, kst_to_utc


class KSTDatetime:
    """KST로 자동 변환되는 datetime 필드를 위한 클래스"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        
        if isinstance(v, datetime):
            # UTC에서 KST로 변환
            return utc_to_kst(v)
        
        return v


def datetime_to_kst_validator(v: Optional[datetime]) -> Optional[datetime]:
    """UTC datetime을 KST로 변환하는 validator"""
    return utc_to_kst(v)


def datetime_from_kst_validator(v: Optional[datetime]) -> Optional[datetime]:
    """KST datetime을 UTC로 변환하는 validator (DB 저장 전)"""
    return kst_to_utc(v)


# Pydantic 모델에서 사용할 필드 타입
KSTDatetimeField = Field(
    default=None,
    description="자동으로 KST로 변환되는 datetime 필드"
)
