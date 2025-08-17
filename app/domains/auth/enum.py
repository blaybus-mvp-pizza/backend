from enum import Enum


class PROVIDER_TYPE(str, Enum):
    GOOGLE = "google"
    KAKAO = "kakao"
    NAVER = "naver"


class PAYMENT_PROVIDER_TYPE(str, Enum):
    TOSSPAY = "tosspay"
    CARD = "card"
    NAVERPAY = "naverpay"
    KAKAOPAY = "kakaopay"
    VIRTUAL = "virtual"
