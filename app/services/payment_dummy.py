from typing import Optional


def charge(amount: float, user_id: int, note: str = "") -> int:
    return 1  # dummy payment id


def refund(payment_id: int, amount: float, note: str = "") -> bool:
    return True


def notify(user_id: int, title: str, body: str) -> None:
    return None
