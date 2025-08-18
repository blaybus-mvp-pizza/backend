from enum import Enum


class ErrorCode(str, Enum):
    AUCTION_NOT_FOUND = "AUCTION_NOT_FOUND"
    BID_NOT_ALLOWED = "BID_NOT_ALLOWED"
    BUY_NOT_ALLOWED = "BUY_NOT_ALLOWED"
