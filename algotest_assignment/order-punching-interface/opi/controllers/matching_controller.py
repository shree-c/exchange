from datetime import datetime
from typing import Literal
from redis import Redis
from csql import OrderCRUD

r = Redis(host="redis")

order_crud = OrderCRUD(r)

TODAY_BUY_QUEUE = f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}"
TODAY_SELLS_QUEUE = f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}"


def calculate_depth_buy(depth, key):
    price_quantity = {}
    index = 0
    while True:
        l = r.zcard(key)
        if l == index:
            break
        if l == 0:
            break
        order_id = r.zrange(key, index, index)[0]
        [status, data] = order_crud.get(order_id.decode())
        if not status:
          continue
        if data:
            price = data['price']
            if len(price_quantity) == depth and str(price) not in price_quantity:
                break
            quantity = data['quantity'] - data['punched']
            if str(price) not in price_quantity:
                price_quantity[str(price)] = quantity
            else:
                price_quantity[str(price)] += quantity
            index += 1
    return price_quantity


def pluck_order_id(side: Literal[1, -1], order_id: str):
    if side == -1:
        r.zrem(TODAY_SELLS_QUEUE, order_id)
    elif side == 1:
        r.zrem(TODAY_BUY_QUEUE, order_id)
