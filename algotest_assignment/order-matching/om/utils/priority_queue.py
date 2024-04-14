from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    item: Any = field(compare=False)


class PQManager:
    def __init__(self, unique_set, pq, last_added_price, priority_order=1) -> None:
        self.unique_set: set = unique_set
        self.pq = pq
        self.priority_order = priority_order
        self.last_added_price = last_added_price

    def put(self, price):
        if price not in self.unique_set._getvalue():
            self.last_added_price.value = price
            self.unique_set.add(price)
            self.pq.put(
                PrioritizedItem(priority=self.priority_order * price, item=price)
            )

    def get(self, no_wait=False):
        if no_wait:
            if self.pq.qsize() == 0:
                return None
        item = self.pq.get().item
        self.unique_set.discard(item)
        return item

