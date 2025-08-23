"""
시간대 변환이 자동으로 적용되는 Base Pydantic 모델
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, field_validator, field_serializer
from app.core.timezone import utc_to_kst, kst_to_utc


class TimezoneAwareModel(BaseModel):
    """
    datetime 필드를 자동으로 KST로 변환하고 문자열로 직렬화하는 Base 모델
    
    - DB에서 읽은 UTC 시간을 KST로 변환하여 API 응답에 사용
    - API 응답 시 YYYY-MM-DD HH:MM:SS 형식으로 문자열 변환
    """
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_datetime_fields_to_kst(cls, v: Any, info) -> Any:
        """모든 datetime 필드를 UTC에서 KST로 변환"""
        if isinstance(v, datetime) and info.field_name:
            # datetime 필드를 KST로 변환
            if info.field_name.endswith('_at') or 'time' in info.field_name.lower():
                return utc_to_kst(v) or v
        return v
    
    @field_serializer('*', when_used='json')
    def serialize_datetime_fields(self, value: Any, info) -> Any:
        """datetime 필드를 YYYY-MM-DD HH:MM:SS 형식 문자열로 직렬화"""
        if isinstance(value, datetime) and info.field_name:
            if info.field_name.endswith('_at') or 'time' in info.field_name.lower():
                return value.strftime("%Y-%m-%d %H:%M:%S")
        return value


class TimezoneInputModel(BaseModel):
    """
    KST 입력을 UTC로 변환하는 Input 모델
    
    클라이언트에서 받은 KST 시간을 UTC로 변환하여 DB에 저장
    """
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_datetime_inputs_to_utc(cls, v: Any, info) -> Any:
        """KST datetime 입력을 UTC로 변환"""
        if isinstance(v, datetime) and info.field_name:
            # datetime 필드를 UTC로 변환
            if info.field_name.endswith('_at') or 'time' in info.field_name.lower():
                return kst_to_utc(v)
        return v


class StringDateTimeModel(BaseModel):
    """
    datetime 필드를 항상 문자열로 직렬화하는 Base 모델
    (Repository에서 이미 KST로 변환된 datetime을 문자열로 변환)
    """
    
    @field_serializer('*', when_used='json')
    def serialize_datetime_fields(self, value: Any, info) -> Any:
        """datetime 필드를 YYYY-MM-DD HH:MM:SS 형식 문자열로 직렬화"""
        if isinstance(value, datetime) and info.field_name:
            if info.field_name.endswith('_at') or 'time' in info.field_name.lower():
                return value.strftime("%Y-%m-%d %H:%M:%S")
        return value


# 편의용 별칭
BaseResponseModel = StringDateTimeModel  # Repository에서 변환 후 사용
BaseRequestModel = TimezoneInputModel
