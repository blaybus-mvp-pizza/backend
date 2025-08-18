from typing import List, Optional


class BidRules:
    @staticmethod
    def calculate_bid_increment(amount: float) -> int:
        if amount < 10_000:
            return 500
        elif amount < 30_000:
            return 1_000
        elif amount < 50_000:
            return 2_000
        elif amount < 150_000:
            return 5_000
        elif amount < 300_000:
            return 10_000
        elif amount < 500_000:
            return 20_000
        elif amount < 1_000_000:
            return 30_000
        else:
            return 50_000

    @classmethod
    def make_bid_steps(
        cls, current: float, buy_now: Optional[float], count: int = 4
    ) -> List[float]:
        if current <= 0:
            return []
        inc = cls.calculate_bid_increment(current)
        steps: List[float] = []
        next_amt = current + inc
        for _ in range(count):
            if buy_now is not None and next_amt >= buy_now:
                break
            steps.append(float(next_amt))
            next_amt += inc
            inc = cls.calculate_bid_increment(next_amt)
        return steps
