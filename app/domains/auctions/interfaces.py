from typing import Protocol, runtime_checkable


@runtime_checkable
class AuctionService(Protocol):
    def place_bid(self, *, auction_id: int, amount: float, user_id: int) -> dict: ...

    def buy_now(self, *, auction_id: int, user_id: int) -> dict: ...
