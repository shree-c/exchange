from redis import Redis
from pprint import pp, pformat, pprint
from datetime import datetime
from csql import Base, OrderCRUD, TradeCRUD
from time import sleep
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

r = Redis(password="shreex")
engine = create_engine("sqlite:///../orders.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
order_crud = OrderCRUD(session=session)


TODAY_BUY_QUEUE = f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}"
TODAY_SELLS_QUEUE = f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}"


def calculate_depth_buy(depth, key):
    price_quantity = {}
    depth_counter = 0
    index = 0
    while True:
        if depth_counter == depth:
            break
        if r.zcard(key) == 0:
            break
        order_id = r.zrange(key, index, index)[0]
        order = order_crud.get(order_id.decode())
        if order:
            price = order.price
            quantity = order.quantity - order.punched
            if str(price) not in price_quantity:
                price_quantity[str(price)] = quantity
            else:
                price_quantity[str(price)] += quantity
            index += 1
        depth_counter += 1
    pass
    return price_quantity


while True:
    TODAY_LTP = f"ltp_{datetime.now().strftime('%Y_%m_%d')}"
    print(
        "BUY",
        r.zcard(TODAY_BUY_QUEUE),
        "SELL",
        r.zcard(TODAY_SELLS_QUEUE),
        f"LTP : {r.get(TODAY_LTP)}",
    )
    pprint(calculate_depth_buy(5, TODAY_BUY_QUEUE))
    pprint(calculate_depth_buy(5, TODAY_SELLS_QUEUE))
    sleep(0.2)
