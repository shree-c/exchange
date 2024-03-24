from csql import OrderCRUD
from datetime import datetime
from time import sleep
from redis import Redis

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

r = Redis( host='redis')

# engine = create_engine("sqlite:///orders.db")
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)
# session = Session()
order_crud = OrderCRUD(r)

SCALE_FACTOR = 1e5


def get_score(price, timestamp, side):
    price_scaled = price * SCALE_FACTOR
    return round(price_scaled - round(timestamp)) * side * -1


def mark_accepted(order_ids):
    order_crud.mark_orders_accepted(order_ids)


r.delete(f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}")
r.delete(f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}")


def insert_them_in_op_list(unaccepted_orders):
    sells = {}
    buys = {}
    [status, data] = order_crud.get_these_orders(unaccepted_orders)
    if not status:
        print("ERROR WHILE INSERTING INTO SORTED SET")
        print(data)
        return
    for order in data:
        score = get_score(order["price"], order["timestamp"], order["side"])
        print(score)
        if order["side"] == -1:
            sells[str(order["order_id"])] = score
        else:
            buys[str(order["order_id"])] = score
    if len(buys) != 0:
        print("adding to buy queue", buys)
        r.zadd(f"sorted_or_buys_{datetime.now().strftime('%Y_%m_%d')}", buys)
    if len(sells) != 0:
        print("adding to sell queue", sells)
        r.zadd(f"sorted_or_sells_{datetime.now().strftime('%Y_%m_%d')}", sells)
    # mark_accepted([*sells.keys(), *buys.keys()])


while True:
    print("Processing start...")
    [status, new_orders] = order_crud.get_all_queued_orders()
    if len(new_orders) > 0:
        insert_them_in_op_list(new_orders)
        order_crud.delete_from_order_process_queue(len(new_orders))
    sleep(0.5)
